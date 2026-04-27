"""
Janitor Disk Inspector — Scanner assíncrono de arquivos residuais.

Roda como background task na inicialização do FastAPI.
Classifica arquivos por padrão e risco, salva relatório em janitor_disk_report.json.
NUNCA deleta automaticamente — apenas lista e move para quarentena mediante aprovação.
"""
import os
import re
import json
import shutil
import asyncio
import time
from pathlib import Path
from typing import Literal

# ── Raízes a varrer ───────────────────────────────────────────────────────────
_BACKEND_ROOT = Path(__file__).parent.parent.parent          # backend/
_PROJECT_ROOT = _BACKEND_ROOT.parent                         # questor_explorer/
_QUARANTINE   = _BACKEND_ROOT / ".janitor_quarantine"
_REPORT_FILE  = _BACKEND_ROOT / "janitor_disk_report.json"

RiskLevel = Literal["safe_delete", "review", "keep"]

# ── Padrões de classificação ──────────────────────────────────────────────────
TRASH_RULES: list[tuple[str, str, RiskLevel]] = [
    # (regex_nome, categoria, risco)
    # Scripts de patch temporários (nunca são imports)
    (r'^patcher\d*\.py$',                     'SCRIPT_PATCH',   'safe_delete'),
    (r'^patcher_(combinatorial|main|master|phase)',  'SCRIPT_PATCH', 'safe_delete'),
    (r'^replace_script',                       'SCRIPT_PATCH',   'safe_delete'),
    (r'^replace_(all|css|fuzzy|hang|jsx|limits|receb|stitch|ui|vendas)', 'SCRIPT_PATCH', 'safe_delete'),
    (r'^replace\d+\.py$',                      'SCRIPT_PATCH',   'safe_delete'),
    (r'^patch\d+\.py$',                        'SCRIPT_PATCH',   'safe_delete'),
    (r'^patch_(frontend|hub|main|receita)',     'SCRIPT_PATCH',   'safe_delete'),
    (r'^fix_(?!poc_concluidas|bugs)',           'SCRIPT_FIX',     'safe_delete'),
    (r'^text_patch\.py$',                      'SCRIPT_PATCH',   'safe_delete'),
    (r'^undo\.py$',                            'SCRIPT_PATCH',   'safe_delete'),

    # Scripts de debug one-shot
    (r'^debug_(?!cno)',                        'DEBUG_SCRIPT',   'safe_delete'),
    (r'^append_',                              'DEBUG_SCRIPT',   'safe_delete'),
    (r'^check_(?!fp)',                         'DEBUG_SCRIPT',   'safe_delete'),
    (r'^dump_(?!questor_contas)',              'DEBUG_SCRIPT',   'safe_delete'),
    (r'^find_(?!indices)',                     'DEBUG_SCRIPT',   'safe_delete'),
    (r'^get_(?!planoespec|poc_columns)',       'DEBUG_SCRIPT',   'safe_delete'),
    (r'^query_(?!check)',                      'DEBUG_SCRIPT',   'safe_delete'),
    (r'^run_(?!cub_check)',                    'DEBUG_SCRIPT',   'safe_delete'),
    (r'^search\d*\.py$',                       'DEBUG_SCRIPT',   'safe_delete'),
    (r'^search_(caixa|conversor|cub|logs|receb)\.py$', 'DEBUG_SCRIPT', 'safe_delete'),
    (r'^verify\.py$',                          'DEBUG_SCRIPT',   'safe_delete'),
    (r'^deep_search\.py$',                     'DEBUG_SCRIPT',   'safe_delete'),

    # Scripts de update temporários
    (r'^update_(?!manifest)',                  'SCRIPT_UPDATE',  'safe_delete'),
    (r'^inject_final\.py$',                   'SCRIPT_UPDATE',  'safe_delete'),
    (r'^inject',                              'SCRIPT_UPDATE',  'safe_delete'),
    (r'^apply_poc',                            'SCRIPT_UPDATE',  'review'),
    (r'^generate_new_endpoint\.py$',           'SCRIPT_UPDATE',  'safe_delete'),

    # Scripts de rebuild/recover
    (r'^rebuild_',                             'SCRIPT_RECOVER', 'safe_delete'),
    (r'^recover_',                             'SCRIPT_RECOVER', 'safe_delete'),
    (r'^emergency_',                           'SCRIPT_RECOVER', 'safe_delete'),
    (r'^ultimate_',                            'SCRIPT_RECOVER', 'safe_delete'),
    (r'^create_hub\.py$',                      'SCRIPT_RECOVER', 'review'),

    # Dumps e outputs de debug temporários
    (r'.*\.(txt|log|out)$',                   'LOG_FILE',       'review'),
    (r'.*\.json$',                             'DUMP_JSON',      'review'),

    # TMP
    (r'^tmp_|^temp_',                          'TMP_FILE',       'safe_delete'),
    (r'^scratch_',                             'TMP_FILE',       'safe_delete'),
]

# Arquivos que NUNCA devem ser tocados
PROTECTED_FILES = {
    "main.py", "requirements.txt", ".env", ".env.example",
    "QuestorExplorer.spec", "gerar_dimob.py", "sindicato_agent.py",
    "cub_agent.py", "vector_engine.py", "vector_sync.py",
    "poc_splink.py", "poc_database.sqlite", "agente_checkpoints.sqlite",
    "janitor_metrics.sqlite", "janitor_disk_report.json",
    "chavejson.json", "meta.json",
    # Configs e docs
    "API_GUIDELINES.md", "scratchpad.md", "debug_cno.md",
    # Scripts reais do backend
    "startup_test.py", "refactor_receitas.py",
}

PROTECTED_DIRS = {
    ".venv", "__pycache__", "core", "parsers", "tools", "build", "dist",
    ".janitor_quarantine",
}


def _classify_file(fname: str) -> tuple[str, RiskLevel] | None:
    """Retorna (categoria, risk) ou None se arquivo deve ser mantido."""
    if fname in PROTECTED_FILES:
        return None
    for pattern, categoria, risk in TRASH_RULES:
        if re.match(pattern, fname, re.IGNORECASE):
            return categoria, risk
    return None


def scan_directory(base_dir: Path, max_age_days: int = 0) -> list[dict]:
    """
    Varre `base_dir` (1 nível) e retorna lista de candidatos a limpeza.
    max_age_days=0 significa que não filtra por data.
    """
    results = []
    now = time.time()
    try:
        for entry in base_dir.iterdir():
            if entry.is_dir():
                if entry.name in PROTECTED_DIRS:
                    continue
                # Varre sub-diretório apenas se não for protegido
                continue  # por segurança, não varre subpastas automaticamente

            fname = entry.name
            classification = _classify_file(fname)
            if classification is None:
                continue

            categoria, risk = classification
            stat = entry.stat()
            age_days = (now - stat.st_mtime) / 86400

            if max_age_days > 0 and age_days < max_age_days:
                continue

            results.append({
                "arquivo":    fname,
                "path":       str(entry),
                "categoria":  categoria,
                "risk":       risk,
                "size_kb":    round(stat.st_size / 1024, 1),
                "age_days":   round(age_days, 1),
                "modified":   time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime)),
            })
    except PermissionError:
        pass
    return results


async def run_disk_scan():
    """Task assíncrona que roda a varredura e salva o relatório."""
    await asyncio.sleep(5)  # aguarda o startup completo do FastAPI
    while True:
        try:
            candidatos = []
            # Varre raiz do projeto
            candidatos.extend(scan_directory(_PROJECT_ROOT))
            # Varre backend/
            candidatos.extend(scan_directory(_BACKEND_ROOT))

            # Agrupa por categoria
            por_categoria: dict[str, list] = {}
            for c in candidatos:
                por_categoria.setdefault(c["categoria"], []).append(c)

            total_kb = sum(c["size_kb"] for c in candidatos)
            safe_delete = [c for c in candidatos if c["risk"] == "safe_delete"]
            review      = [c for c in candidatos if c["risk"] == "review"]

            relatorio = {
                "gerado_em":       time.strftime("%Y-%m-%dT%H:%M:%S"),
                "total_arquivos":  len(candidatos),
                "total_size_kb":   round(total_kb, 1),
                "safe_delete_count": len(safe_delete),
                "review_count":    len(review),
                "por_categoria":   {k: len(v) for k, v in por_categoria.items()},
                "candidatos":      sorted(candidatos, key=lambda x: x["size_kb"], reverse=True),
            }

            with open(_REPORT_FILE, "w", encoding="utf-8") as f:
                json.dump(relatorio, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[Janitor] Disk scan error: {e}")

        # Re-varre a cada 30 minutos
        await asyncio.sleep(1800)


def get_disk_report() -> dict:
    """Retorna o relatório mais recente (lê do arquivo JSON)."""
    if not _REPORT_FILE.exists():
        return {"status": "pending", "message": "Varredura ainda não concluída (aguarde ~5s após startup)"}
    with open(_REPORT_FILE, encoding="utf-8") as f:
        return json.load(f)


def move_to_quarantine(paths: list[str]) -> dict:
    """
    Move os arquivos especificados para .janitor_quarantine/.
    Cria a pasta se não existir. Retorna resultado por arquivo.
    """
    _QUARANTINE.mkdir(exist_ok=True)
    results = []
    for p in paths:
        src = Path(p)
        if not src.exists():
            results.append({"arquivo": src.name, "status": "not_found"})
            continue
        # Proteção extra: nunca move arquivo protegido
        if src.name in PROTECTED_FILES:
            results.append({"arquivo": src.name, "status": "protected"})
            continue
        dst = _QUARANTINE / src.name
        # Se já existe na quarentena, adiciona timestamp
        if dst.exists():
            stem = dst.stem
            suffix = dst.suffix
            dst = _QUARANTINE / f"{stem}_{int(time.time())}{suffix}"
        try:
            shutil.move(str(src), str(dst))
            results.append({"arquivo": src.name, "status": "moved", "dest": str(dst)})
        except Exception as e:
            results.append({"arquivo": src.name, "status": "error", "detail": str(e)})

    # Atualiza relatório após mover
    try:
        report = get_disk_report()
        if isinstance(report, dict) and "candidatos" in report:
            moved_names = {r["arquivo"] for r in results if r["status"] == "moved"}
            report["candidatos"] = [c for c in report["candidatos"] if c["arquivo"] not in moved_names]
            report["total_arquivos"] = len(report["candidatos"])
            report["total_size_kb"] = round(sum(c["size_kb"] for c in report["candidatos"]), 1)
            report["safe_delete_count"] -= len(moved_names)
            with open(_REPORT_FILE, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return {
        "quarentena": str(_QUARANTINE),
        "movidos": len([r for r in results if r["status"] == "moved"]),
        "erros":   len([r for r in results if r["status"] == "error"]),
        "detalhes": results,
    }
