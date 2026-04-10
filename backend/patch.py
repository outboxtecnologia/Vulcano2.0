import re

with open(r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\main.py", "r", encoding="utf-8") as f:
    code = f.read()

# Locate the function exactly
start_idx = code.find('@app.post("/api/auditoria/diagnostico")')
if start_idx == -1:
    print("Function start not found")

end_idx = code.find('@app.get("/api/questor/saldo-contas")')
if end_idx == -1:
    print("Function end not found")

new_func = """@app.post("/api/auditoria/diagnostico")
async def api_auditoria_diagnostico(data: DiagnosticoInput):
    \"\"\"
    Analisa divergências entre Questor (LCTOCTB) e Vulcano (contabilizacoes)
    usando:
      • DuckDB  — JOIN analítico em DataFrames (sem novo banco)
      • PyOD    — IsolationForest por conta (anomaly_score 0-1)
      • LevelShift — detecta QUANDO a divergência começou (numpy nativo)
      • KMeans  — classifica o PADRÃO da divergência por conta
      • LLM Gemini — Formulação de causa raiz das principais anomalias
    \"\"\"
    import warnings, logging, asyncio
    warnings.filterwarnings("ignore")

    try:
        import pandas as pd
        import numpy as np

        if not data.linhas:
            return {"contas": [], "summary": "Nenhum dado enviado para análise."}

        # Nomes das contas (Questor)
        conn_q = get_conn("questor")
        cur_q = conn_q.cursor()
        cur_q.execute("SELECT CONTACTB, DESCRCONTA FROM PLANOESPEC WHERE CODIGOEMPRESA = ?", (data.empresa_id,))
        plano = {int(r[0]): str(r[1] or "").strip() for r in cur_q.fetchall() if r[0]}
        conn_q.close()

        def _sync_ml_core():
            import duckdb
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            from pyod.models.iforest import IForest

            df_todas = pd.DataFrame([r.dict() for r in data.linhas])
            df_q = df_todas[["conta_id", "competencia", "saldo_q", "n_lanc_q"]].copy()
            df_v = df_todas[["conta_id", "competencia", "saldo_v", "n_lanc_v"]].copy()

            df_q["conta_id"] = pd.to_numeric(df_q["conta_id"], errors="coerce")
            df_v["conta_id"] = pd.to_numeric(df_v["conta_id"], errors="coerce")
            df_q = df_q.dropna(subset=["conta_id"])
            df_v = df_v.dropna(subset=["conta_id"])
            df_q["conta_id"] = df_q["conta_id"].astype(int)
            df_v["conta_id"] = df_v["conta_id"].astype(int)

            if df_q.empty and df_v.empty:
                return [], 0, 0, 0, 0

            ddb = duckdb.connect()
            delta_df = ddb.execute(\"\"\"
                SELECT
                    COALESCE(q.conta_id, v.conta_id) AS conta_id,
                    COALESCE(q.competencia, v.competencia) AS competencia,
                    COALESCE(q.saldo_q, 0.0) AS saldo_q,
                    COALESCE(v.saldo_v, 0.0) AS saldo_v,
                    COALESCE(q.saldo_q, 0.0) - COALESCE(v.saldo_v, 0.0) AS delta,
                    COALESCE(q.n_lanc_q, 0) AS n_lanc_q,
                    COALESCE(v.n_lanc_v, 0) AS n_lanc_v,
                    ABS(COALESCE(q.saldo_q, 0.0) - COALESCE(v.saldo_v, 0.0)) AS abs_delta
                FROM df_q q
                FULL OUTER JOIN df_v v ON q.conta_id = v.conta_id AND q.competencia = v.competencia
                ORDER BY conta_id, competencia
            \"\"\").fetchdf()

            if delta_df.empty:
                return [], 0, 0, 0, 0

            features_df = ddb.execute(\"\"\"
                SELECT
                    conta_id,
                    AVG(delta)                              AS media_delta,
                    STDDEV(delta)                           AS std_delta,
                    MAX(abs_delta)                          AS max_delta_abs,
                    AVG(abs_delta)                          AS media_abs_delta,
                    SUM(CASE WHEN abs_delta > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                                                            AS pct_meses_divergentes,
                    COUNT(*)                                AS n_meses,
                    AVG(n_lanc_q)                           AS avg_lanc_questor,
                    AVG(n_lanc_v)                           AS avg_lanc_vulcano
                FROM delta_df
                GROUP BY conta_id
                HAVING COUNT(*) >= 2
            \"\"\").fetchdf()

            if features_df.empty or len(features_df) < 3:
                return [], -1, 0, 0, 0

            _feat_cols = ["media_delta", "std_delta", "max_delta_abs", "pct_meses_divergentes", "avg_lanc_questor"]
            X = features_df[_feat_cols].fillna(0).values
            X_scaled = StandardScaler().fit_transform(X)

            contamination = min(0.2, max(0.05, 3 / len(X)))
            iso = IForest(contamination=contamination, random_state=42, n_estimators=100)
            iso.fit(X_scaled)

            scores_raw = iso.decision_scores_
            min_s, max_s = scores_raw.min(), scores_raw.max()
            scores_norm = (scores_raw - min_s) / (max_s - min_s + 1e-9)
            features_df["anomaly_score"] = scores_norm.round(3)
            features_df["anomaly_label"] = np.where(iso.labels_ == 1, "ANOMALIA", "NORMAL")

            n_clusters = min(4, max(2, len(features_df) // 2))
            km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            features_df["cluster"] = km.fit_predict(X_scaled)

            _CLUSTER_LABELS = {0: "Exato", 1: "Lag Temporal", 2: "Percentual Fixo", 3: "Caótico"}
            _centroid_stds = km.cluster_centers_[:, 1]
            _order = np.argsort(_centroid_stds)
            _label_map = {int(_order[i]): _CLUSTER_LABELS[i] for i in range(n_clusters)}
            features_df["padrao"] = features_df["cluster"].map(_label_map).fillna("Outro")

            def _detect_level_shift(series: pd.Series, window: int = 3) -> dict | None:
                if len(series) < window * 2 + 1: return None
                vals = series.values.astype(float)
                best_i, best_score = 0, 0.0
                for i in range(window, len(vals) - window):
                    score = abs(np.mean(vals[i:i + window]) - np.mean(vals[max(0, i - window):i]))
                    if score > best_score:
                        best_score, best_i = score, i
                if best_score < 1.0: return None
                return {
                    "competencia": series.index[best_i] if hasattr(series.index, '__getitem__') else str(best_i),
                    "delta_antes": round(float(np.mean(vals[:best_i])), 2),
                    "delta_depois": round(float(np.mean(vals[best_i:])), 2),
                    "magnitude": round(float(best_score), 2)
                }

            shifts = {}
            for conta_id, grp in delta_df.sort_values("competencia").groupby("conta_id"):
                serie = grp.set_index("competencia")["delta"]
                sh = _detect_level_shift(serie)
                if sh: shifts[int(conta_id)] = sh
            
            meses_unicos = int(df_todas["competencia"].nunique() if not df_todas.empty else 0)

            top_contas = features_df.sort_values("anomaly_score", ascending=False).head(data.top_n)
            resultado = []
            for _, row in top_contas.iterrows():
                cid = int(row["conta_id"])
                resultado.append({
                    "conta_id":               cid,
                    "conta_nome":             plano.get(cid, f"Conta {cid}"),
                    "anomaly_score":          round(float(row["anomaly_score"]), 3),
                    "anomaly_label":          row["anomaly_label"],
                    "padrao":                 row["padrao"],
                    "media_delta":            round(float(row["media_delta"]), 2),
                    "std_delta":              round(float(row.get("std_delta") or 0), 2),
                    "max_delta_abs":          round(float(row["max_delta_abs"]), 2),
                    "pct_meses_divergentes":  round(float(row["pct_meses_divergentes"]), 1),
                    "n_meses_analisados":     int(row["n_meses"]),
                    "avg_lanc_questor":       round(float(row.get("avg_lanc_questor") or 0), 1),
                    "avg_lanc_vulcano":       round(float(row.get("avg_lanc_vulcano") or 0), 1),
                    "level_shift":            shifts.get(cid),
                })
            return resultado, int((features_df["anomaly_label"] == "ANOMALIA").sum()), meses_unicos, len(features_df), len(shifts)

        # Executa a parte bloqueante (ML e Processamento de Dados) em thread controlada
        resultado, n_anomalias, meses_unicos, len_feat, len_shifts = await asyncio.to_thread(_sync_ml_core)

        if len_feat == 0: return {"contas": [], "summary": "Sem cruzamento de dados no período."}
        if len_feat == -1: return {"contas": [], "summary": "Dados insuficientes para análise ML (mínimo 3 contas, 2 meses)."}

        # ── 9. Investigação Qualitativa Gemini nas Top Anomalias ────────────
        anomalias = [r for r in resultado if r["anomaly_label"] == "ANOMALIA"][:5] # Top 5 anomalias
        
        if anomalias:
            schema = '{"causas":[{"conta_id":0,"causa_raiz":"","recomendacao":""}]}'
            prompt = "Você é um auditor contábil sênior diagnosticando as divergências entre o ERP Questor (físico, saldos lançados) e o motor societário Vulcano (virtual, espelho da POC IFRS e impostos gerados). \\n"
            prompt += "Baseado no comportamento quantitativo (Padrão, Delta, Level-Shift), explique a possível causa raiz da anomalia de cada conta e dê uma recomendação de ação.\\n\\nContas a Analisar:\\n"
            
            for a in anomalias:
                cid = a["conta_id"]
                df_conta = pd.DataFrame([r.dict() for r in data.linhas if r.conta_id == cid]).sort_values("competencia")
                serie_txt = df_conta[["competencia", "saldo_q", "saldo_v"]].to_csv(index=False, sep="|")
                
                sh = a["level_shift"]
                shift_str = f"Iniciou {sh['competencia']} (Antes: {sh['delta_antes']}, Depois: {sh['delta_depois']})" if sh else "Nenhum"
                
                prompt += f"--- CONTA {cid} ({a['conta_nome']}) ---\\n"
                prompt += f"Padrão Algorítmico: {a['padrao']}, Shift de Nível: {shift_str}\\nSérie Mensal (Q=Questor vs V=Vulcano):\\n{serie_txt}\\n\\n"

            prompt += f"Retorne **apenas** JSON respeitando estritamente o schema: {schema}"
            
            try:
                resp_ia = await _gemini_generate_json_async(prompt)
                for causa in resp_ia.get("causas", []):
                    c_id = causa.get("conta_id")
                    match = next((r for r in resultado if r["conta_id"] == c_id), None)
                    if match:
                        match["causa_raiz"] = str(causa.get("causa_raiz", ""))
                        match["recomendacao"] = str(causa.get("recomendacao", ""))
            except Exception as ml_err:
                logging.error(f"Erro na inferência qualitativa do Gemini: {ml_err}")

        return {
            "contas":    resultado,
            "total_contas_analisadas": len_feat,
            "total_anomalias": n_anomalias,
            "janela_meses": meses_unicos,
            "summary": (
                f"{len_feat} contas analisadas ({meses_unicos} meses). "
                f"{n_anomalias} contas anômalas detectadas. "
                f"{len_shifts} com mudança de nível identificada."
            )
        }

    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
"""

patched_code = code[:start_idx] + new_func + "\n" + code[end_idx:]

with open(r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\main.py", "w", encoding="utf-8") as f:
    f.write(patched_code)

print("Patched main.py successfully.")
