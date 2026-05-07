import React, { useState, useEffect } from "react";
import {
  Layers,
  RefreshCw,
  AlertCircle,
  TrendingUp,
  ChevronDown,
  Plus,
} from "lucide-react";
import { API_BASE } from "./apiBase";

const formatCurrency = (val) => {
  if (val === null || val === undefined) return "R$ 0,00";
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(val);
};

export const TributosGlobaisView = ({ selectedEmpresa }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dataIni, setDataIni] = useState(`${new Date().getFullYear()}-01`);
  const [dataFim, setDataFim] = useState("");
  const [fetchTrigger, setFetchTrigger] = useState(0);
  const [expandedRow, setExpandedRow] = useState(null);
  const [regimeFilter, setRegimeFilter] = useState("TODOS");

  const isFiltered = Boolean(dataIni || dataFim);

  useEffect(() => {
    if (!selectedEmpresa) return;
    setLoading(true);
    setError(null);

    fetch(
      `${API_BASE}/api/receitas-caixa?empresa_id=${selectedEmpresa}${dataIni ? `&data_ini=${dataIni}` : ""}${dataFim ? `&data_fim=${dataFim}` : ""}`,
    )
      .then((res) => {
        if (!res.ok) throw new Error(`Erro HTTP: ${res.status}`);
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [selectedEmpresa, fetchTrigger]);

  let totalCaixaAcumulado = 0;
  let totalSocAcumulado = 0;
  let dashboardMetaKeys = [];
  if (data?.dashboard_meta) {
    dashboardMetaKeys = Object.keys(data.dashboard_meta);
    Object.values(data.dashboard_meta).forEach((meta) => {
      totalCaixaAcumulado += meta.tributos_caixa_acumulado || 0;
      totalSocAcumulado += meta.tributos_soc_acumulado || 0;
    });
  }
  const saldoDiferimento = totalSocAcumulado - totalCaixaAcumulado;

  const filteredRows = Object.entries(data?.dashboard_meta || {}).filter(
    ([name, meta]) => {
      const pisCofins = (meta.pis || 0) + (meta.cofins || 0);
      const ret = meta.ret || 0;
      const isRet = ret > 0 && pisCofins === 0;
      if (regimeFilter === "PRESUMIDO" && isRet) return false;
      if (regimeFilter === "RET 4%" && !isRet) return false;
      return true;
    },
  );

  return (
    <div
      style={{
        flex: "1 1 0%",
        display: "flex",
        flexDirection: "column",
        minWidth: 0,
        height: "100%",
      }}
    >
      {/* NOVO HEADER */}
      <header
        style={{
          borderBottom: "1px solid rgba(255, 160, 80, 0.08)",
          background: "rgb(18, 16, 14)",
          padding: "12px 16px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "9px",
            paddingRight: "14px",
            borderRight: "1px solid rgba(255, 160, 80, 0.08)",
          }}
        >
          <div
            className="pulse"
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              background: "rgb(255, 122, 26)",
              boxShadow: "rgb(255, 122, 26) 0px 0px 8px",
            }}
          ></div>
          <span
            style={{
              fontFamily: '"JetBrains Mono"',
              fontSize: "10px",
              letterSpacing: "0.22em",
              color: "rgb(240, 230, 216)",
            }}
          >
            TRIBUTOS GLOBAIS
          </span>
          <span
            style={{
              fontFamily: '"JetBrains Mono"',
              fontSize: "10px",
              color: "rgb(90, 78, 66)",
            }}
          >
            · {dashboardMetaKeys.length} obras
          </span>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "5px 10px 5px 12px",
            borderRadius: "7px",
            background: "rgba(255, 140, 42, 0.08)",
            border: "1px solid rgba(255, 140, 42, 0.3)",
          }}
        >
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span
              style={{
                fontFamily: '"JetBrains Mono"',
                fontSize: "8.5px",
                letterSpacing: "0.2em",
                color: "rgb(90, 78, 66)",
                lineHeight: 1,
              }}
            >
              COMPETÊNCIA INI
            </span>
            <input
              type="month"
              value={dataIni}
              onChange={(e) => setDataIni(e.target.value)}
              style={{
                background: "transparent",
                border: "none",
                outline: "none",
                color: "rgb(240, 230, 216)",
                fontFamily: '"JetBrains Mono"',
                fontSize: "11.5px",
                padding: "2px 0 0",
                width: "88px",
              }}
            />
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "5px 10px 5px 12px",
            borderRadius: "7px",
            background: "rgb(26, 22, 20)",
            border: "1px solid rgba(255, 160, 80, 0.08)",
          }}
        >
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span
              style={{
                fontFamily: '"JetBrains Mono"',
                fontSize: "8.5px",
                letterSpacing: "0.2em",
                color: "rgb(90, 78, 66)",
                lineHeight: 1,
              }}
            >
              COMPETÊNCIA FIM
            </span>
            <input
              type="month"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              placeholder="aberto"
              style={{
                background: "transparent",
                border: "none",
                outline: "none",
                color: "rgb(240, 230, 216)",
                fontFamily: '"JetBrains Mono"',
                fontSize: "11.5px",
                padding: "2px 0 0",
                width: "88px",
              }}
            />
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            background: "rgb(26, 22, 20)",
            border: "1px solid rgba(255, 160, 80, 0.08)",
            borderRadius: "7px",
            padding: "3px",
            gap: "2px",
          }}
        >
          <button
            onClick={() => setRegimeFilter("TODOS")}
            style={{
              padding: "5px 10px",
              borderRadius: "5px",
              cursor: "pointer",
              background:
                regimeFilter === "TODOS"
                  ? "linear-gradient(135deg, rgba(255, 122, 26, 0.2), rgba(201, 58, 18, 0.1))"
                  : "transparent",
              border:
                regimeFilter === "TODOS"
                  ? "1px solid rgba(255, 140, 42, 0.35)"
                  : "1px solid transparent",
              color:
                regimeFilter === "TODOS"
                  ? "rgb(255, 122, 26)"
                  : "rgb(138, 122, 104)",
              fontFamily: '"JetBrains Mono"',
              fontSize: "10px",
              letterSpacing: "0.16em",
            }}
          >
            TODOS
          </button>
          <button
            onClick={() => setRegimeFilter("PRESUMIDO")}
            style={{
              padding: "5px 10px",
              borderRadius: "5px",
              cursor: "pointer",
              background:
                regimeFilter === "PRESUMIDO"
                  ? "linear-gradient(135deg, rgba(255, 122, 26, 0.2), rgba(201, 58, 18, 0.1))"
                  : "transparent",
              border:
                regimeFilter === "PRESUMIDO"
                  ? "1px solid rgba(255, 140, 42, 0.35)"
                  : "1px solid transparent",
              color:
                regimeFilter === "PRESUMIDO"
                  ? "rgb(255, 122, 26)"
                  : "rgb(138, 122, 104)",
              fontFamily: '"JetBrains Mono"',
              fontSize: "10px",
              letterSpacing: "0.16em",
            }}
          >
            PRESUMIDO
          </button>
          <button
            onClick={() => setRegimeFilter("RET 4%")}
            style={{
              padding: "5px 10px",
              borderRadius: "5px",
              cursor: "pointer",
              background:
                regimeFilter === "RET 4%"
                  ? "linear-gradient(135deg, rgba(255, 122, 26, 0.2), rgba(201, 58, 18, 0.1))"
                  : "transparent",
              border:
                regimeFilter === "RET 4%"
                  ? "1px solid rgba(255, 140, 42, 0.35)"
                  : "1px solid transparent",
              color:
                regimeFilter === "RET 4%"
                  ? "rgb(255, 122, 26)"
                  : "rgb(138, 122, 104)",
              fontFamily: '"JetBrains Mono"',
              fontSize: "10px",
              letterSpacing: "0.16em",
            }}
          >
            RET 4%
          </button>
        </div>

        <div style={{ flex: "1 1 0%" }}></div>

        <button
          onClick={() => setFetchTrigger((prev) => prev + 1)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "8px 14px",
            borderRadius: "7px",
            background:
              "linear-gradient(135deg, rgb(255, 122, 26), rgb(201, 58, 18))",
            border: "none",
            color: "rgb(26, 10, 4)",
            fontSize: "12px",
            fontWeight: 600,
            fontFamily: "Inter",
            cursor: "pointer",
            whiteSpace: "nowrap",
            boxShadow:
              "rgba(201, 58, 18, 0.35) 0px 4px 12px, rgba(255, 220, 180, 0.4) 0px 1px 0px inset",
          }}
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />{" "}
          <span> Atualizar matriz </span>
        </button>
      </header>

      <div style={{ flex: "1 1 0%", display: "flex", minHeight: 0 }}>
        <div style={{ flex: "1 1 0%", minWidth: 0, overflowY: "auto" }}>
          <div style={{ padding: "24px 24px 16px" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                marginBottom: "8px",
              }}
            >
              <div
                style={{
                  width: "34px",
                  height: "34px",
                  borderRadius: "8px",
                  background:
                    "linear-gradient(135deg, rgba(255, 122, 26, 0.2), rgba(201, 58, 18, 0.1))",
                  border: "1px solid rgba(255, 140, 42, 0.3)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "rgba(255, 140, 42, 0.18) 0px 0px 18px",
                }}
              >
                <Layers className="text-[rgb(255,122,26)]" size={18} />
              </div>
              <h1
                style={{
                  fontFamily: '"Space Grotesk"',
                  fontWeight: 600,
                  fontSize: "22px",
                  letterSpacing: "-0.01em",
                  color: "rgb(240, 230, 216)",
                }}
              >
                Tributos Globais{" "}
                <span style={{ color: "rgb(90, 78, 66)", fontWeight: 400 }}>
                  · Caixa vs Competência
                </span>
              </h1>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "5px",
                  padding: "3px 8px",
                  borderRadius: "3px",
                  background: "rgba(255, 122, 26, 0.12)",
                  color: "rgb(255, 122, 26)",
                  border: "1px solid rgba(255, 122, 26, 0.3)",
                  fontFamily: '"JetBrains Mono", monospace',
                  fontSize: "10px",
                  fontWeight: 600,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                }}
              >
                PRES vs RET
              </span>
            </div>
            <div
              style={{
                fontSize: "12.5px",
                color: "rgb(138, 122, 104)",
                lineHeight: 1.55,
                maxWidth: "780px",
                paddingLeft: "44px",
              }}
            >
              Apuração Presumido{" "}
              <span
                style={{
                  color: "rgb(240, 230, 216)",
                  fontFamily: '"JetBrains Mono"',
                  fontSize: "11px",
                }}
              >
                (PIS 0,65% · COFINS 3% · CSLL 1,08% · IRPJ 1,2% + 10%)
              </span>{" "}
              versus <span style={{ color: "rgb(240, 230, 216)" }}>RET 4%</span>{" "}
              — diferimento entre regime de competência (faturamento societário)
              e regime de caixa (recebimento fiscal).
            </div>
          </div>

          {loading && !data && (
            <div className="flex-1 flex flex-col items-center justify-center p-12 space-y-4">
              <RefreshCw
                className="animate-spin text-[rgb(255,122,26)]"
                size={48}
              />
              <p className="text-[10px] uppercase font-bold tracking-[0.3em] text-[var(--v-text-muted)]">
                Calculando Matriz Tributária...
              </p>
            </div>
          )}

          {error && (
            <div className="m-6 bg-[var(--v-error)]/10 text-[var(--v-error)] border border-[var(--v-error)]/30 p-4 rounded-[10px] flex items-center gap-3">
              <AlertCircle size={20} />{" "}
              <span className="text-sm font-bold">{error}</span>
            </div>
          )}

          {!loading && !error && data && (
            <>
              {/* KPI CARDS */}
              <div style={{ padding: "0px 24px 22px" }}>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr 1fr",
                    gap: "14px",
                  }}
                >
                  <div
                    style={{
                      position: "relative",
                      overflow: "hidden",
                      background: "rgb(26, 22, 20)",
                      borderWidth: "1px 1px 1px 3px",
                      borderStyle: "solid",
                      borderColor:
                        "rgba(255, 160, 80, 0.08) rgba(255, 160, 80, 0.08) rgba(255, 160, 80, 0.08) rgb(255, 122, 26)",
                      borderRadius: "10px",
                      padding: "16px 18px",
                    }}
                  >
                    <div
                      style={{
                        position: "absolute",
                        top: "-30px",
                        right: "-30px",
                        width: "120px",
                        height: "120px",
                        background:
                          "radial-gradient(circle, rgba(255, 122, 26, 0.12), transparent 70%)",
                        pointerEvents: "none",
                      }}
                    ></div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        marginBottom: "10px",
                      }}
                    >
                      <span
                        style={{
                          fontFamily: '"JetBrains Mono"',
                          fontSize: "9.5px",
                          letterSpacing: "0.22em",
                          color: "rgb(90, 78, 66)",
                        }}
                      >
                        BASE ACUM. FATURAMENTO
                      </span>
                    </div>
                    <div
                      style={{
                        fontFamily: '"Space Grotesk"',
                        fontSize: "24px",
                        fontWeight: 600,
                        color: "rgb(240, 230, 216)",
                        fontVariantNumeric: "tabular-nums",
                        letterSpacing: "-0.01em",
                      }}
                    >
                      {formatCurrency(totalSocAcumulado)}
                    </div>
                    <div
                      style={{
                        fontSize: "11px",
                        color: "rgb(138, 122, 104)",
                        marginTop: "6px",
                      }}
                    >
                      Regime de competência (Soc.)
                    </div>
                  </div>
                  <div
                    style={{
                      position: "relative",
                      overflow: "hidden",
                      background: "rgb(26, 22, 20)",
                      borderWidth: "1px 1px 1px 3px",
                      borderStyle: "solid",
                      borderColor:
                        "rgba(255, 160, 80, 0.08) rgba(255, 160, 80, 0.08) rgba(255, 160, 80, 0.08) rgb(255, 122, 26)",
                      borderRadius: "10px",
                      padding: "16px 18px",
                    }}
                  >
                    <div
                      style={{
                        position: "absolute",
                        top: "-30px",
                        right: "-30px",
                        width: "120px",
                        height: "120px",
                        background:
                          "radial-gradient(circle, rgba(255, 122, 26, 0.12), transparent 70%)",
                        pointerEvents: "none",
                      }}
                    ></div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        marginBottom: "10px",
                      }}
                    >
                      <span
                        style={{
                          fontFamily: '"JetBrains Mono"',
                          fontSize: "9.5px",
                          letterSpacing: "0.22em",
                          color: "rgb(90, 78, 66)",
                        }}
                      >
                        TOTAL ACUM. A RECOLHER
                      </span>
                    </div>
                    <div
                      style={{
                        fontFamily: '"Space Grotesk"',
                        fontSize: "24px",
                        fontWeight: 600,
                        color: "rgb(255, 122, 26)",
                        fontVariantNumeric: "tabular-nums",
                        letterSpacing: "-0.01em",
                      }}
                    >
                      {formatCurrency(totalCaixaAcumulado)}
                    </div>
                    <div
                      style={{
                        fontSize: "11px",
                        color: "rgb(138, 122, 104)",
                        marginTop: "6px",
                      }}
                    >
                      Regime de caixa (Fiscal)
                    </div>
                  </div>
                  <div
                    style={{
                      position: "relative",
                      overflow: "hidden",
                      background: "rgb(26, 22, 20)",
                      borderWidth: "1px 1px 1px 3px",
                      borderStyle: "solid",
                      borderColor:
                        "rgba(255, 160, 80, 0.08) rgba(255, 160, 80, 0.08) rgba(255, 160, 80, 0.08) rgb(255, 194, 71)",
                      borderRadius: "10px",
                      padding: "16px 18px",
                    }}
                  >
                    <div
                      style={{
                        position: "absolute",
                        top: "-30px",
                        right: "-30px",
                        width: "120px",
                        height: "120px",
                        background:
                          "radial-gradient(circle, rgba(255, 194, 71, 0.12), transparent 70%)",
                        pointerEvents: "none",
                      }}
                    ></div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        marginBottom: "10px",
                      }}
                    >
                      <span
                        style={{
                          fontFamily: '"JetBrains Mono"',
                          fontSize: "9.5px",
                          letterSpacing: "0.22em",
                          color: "rgb(90, 78, 66)",
                        }}
                      >
                        SALDO DIFERIMENTO FISCAL
                      </span>
                    </div>
                    <div
                      style={{
                        fontFamily: '"Space Grotesk"',
                        fontSize: "24px",
                        fontWeight: 600,
                        color: "rgb(255, 194, 71)",
                        fontVariantNumeric: "tabular-nums",
                        letterSpacing: "-0.01em",
                      }}
                    >
                      {formatCurrency(saldoDiferimento)}
                    </div>
                    <div
                      style={{
                        fontSize: "11px",
                        color: "rgb(138, 122, 104)",
                        marginTop: "6px",
                      }}
                    >
                      Provisão · ativo diferido
                    </div>
                  </div>
                </div>
              </div>

              {/* GRID TABELA */}
              <div style={{ padding: "0px 24px 22px" }}>
                <div
                  style={{
                    background: "rgb(26, 22, 20)",
                    border: "1px solid rgba(255, 160, 80, 0.08)",
                    borderRadius: "10px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      padding: "14px 18px",
                      borderBottom: "1px solid rgba(255, 160, 80, 0.08)",
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                    }}
                  >
                    <span
                      style={{
                        fontFamily: '"JetBrains Mono"',
                        fontSize: "10.5px",
                        letterSpacing: "0.22em",
                        color: "rgb(240, 230, 216)",
                      }}
                    >
                      MATRIZ POR EMPREENDIMENTO
                    </span>
                    <span
                      style={{
                        width: "1px",
                        height: "12px",
                        background: "rgba(255, 160, 80, 0.08)",
                      }}
                    ></span>
                    <span
                      style={{
                        fontFamily: '"JetBrains Mono"',
                        fontSize: "10px",
                        color: "rgb(90, 78, 66)",
                      }}
                    >
                      {filteredRows.length} obras ·{" "}
                      {isFiltered ? "período filtrado" : "período aberto"}
                    </span>
                  </div>
                  <div style={{ overflowX: "auto" }}>
                    <div style={{ minWidth: "1100px" }}>
                      {/* GRID HEADER */}
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns:
                            "minmax(220px, 1.6fr) 70px 1fr 1fr 1fr 1fr 1.1fr 1.1fr 130px",
                          padding: "10px 18px",
                          borderBottom: "1px solid rgba(255, 160, 80, 0.08)",
                          background: "rgba(0, 0, 0, 0.22)",
                          fontFamily: '"JetBrains Mono"',
                          fontSize: "9.5px",
                          letterSpacing: "0.18em",
                          color: "rgb(90, 78, 66)",
                        }}
                      >
                        <span>OBRA / EMPREENDIMENTO</span>
                        <span style={{ textAlign: "center" }}>REGIME</span>
                        <span style={{ textAlign: "right" }}>PIS/COFINS</span>
                        <span style={{ textAlign: "right" }}>CSLL+IRPJ</span>
                        <span
                          style={{
                            textAlign: "right",
                            color: "rgb(255, 194, 71)",
                          }}
                        >
                          ADIC. IR (10%)
                        </span>
                        <span
                          style={{
                            textAlign: "right",
                            color: "rgb(61, 214, 140)",
                          }}
                        >
                          RET 4%
                        </span>
                        <span style={{ textAlign: "right" }}>TRIB. SOC.</span>
                        <span style={{ textAlign: "right" }}>TRIB. FISCAL</span>
                        <span style={{ textAlign: "center" }}>STATUS</span>
                      </div>

                      {/* GRID ROWS */}
                      {filteredRows.map(([name, meta], idx) => {
                        const pisCofins = (meta.pis || 0) + (meta.cofins || 0);
                        const csllIrpj = (meta.csll || 0) + (meta.irpj || 0);
                        const ret = meta.ret || 0;
                        const isRet = ret > 0 && pisCofins === 0;

                        const balSoc = meta.tributos_soc_acumulado || 0;
                        const balFiscal = meta.tributos_caixa_acumulado || 0;
                        const statusDiff = balSoc - balFiscal;

                        const mesSoc = isFiltered
                          ? meta.tributos_soc_mes
                          : balSoc;
                        const mesFiscal = isFiltered
                          ? meta.tributos_caixa_mes
                          : balFiscal;

                        let isAntecipado = statusDiff < -10;
                        let isDiferido = statusDiff > 10;

                        return (
                          <React.Fragment key={idx}>
                            <button
                              onClick={() =>
                                setExpandedRow(expandedRow === idx ? null : idx)
                              }
                              style={{
                                position: "relative",
                                width: "100%",
                                display: "grid",
                                gridTemplateColumns:
                                  "minmax(220px, 1.6fr) 70px 1fr 1fr 1fr 1fr 1.1fr 1.1fr 130px",
                                alignItems: "center",
                                padding: "11px 18px",
                                background:
                                  expandedRow === idx
                                    ? "rgba(255, 160, 80, 0.05)"
                                    : "transparent",
                                borderTop: "none",
                                borderLeft: "none",
                                borderRight: "none",
                                borderBottom:
                                  "1px solid rgba(255, 160, 80, 0.08)",
                                cursor: "pointer",
                                textAlign: "left",
                                color: "rgb(240, 230, 216)",
                                transition: "background 0.2s",
                              }}
                            >
                              <div
                                style={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "10px",
                                  minWidth: 0,
                                }}
                              >
                                <span
                                  style={{
                                    width: "22px",
                                    height: "22px",
                                    flexShrink: 0,
                                    borderRadius: "5px",
                                    background:
                                      "linear-gradient(135deg, rgba(255, 122, 26, 0.22), rgba(201, 58, 18, 0.12))",
                                    border:
                                      "1px solid rgba(255, 140, 42, 0.22)",
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                  }}
                                >
                                  {expandedRow === idx ? (
                                    <ChevronDown
                                      size={12}
                                      className="text-[rgb(255,122,26)]"
                                    />
                                  ) : (
                                    <Plus
                                      size={12}
                                      className="text-[rgb(255,122,26)]"
                                    />
                                  )}
                                </span>
                                <span
                                  style={{
                                    fontSize: "12.5px",
                                    color: "rgb(240, 230, 216)",
                                    overflow: "hidden",
                                    textOverflow: "ellipsis",
                                    whiteSpace: "nowrap",
                                  }}
                                >
                                  {name}
                                </span>
                              </div>
                              <div style={{ textAlign: "center" }}>
                                {isRet ? (
                                  <span
                                    style={{
                                      fontFamily: '"JetBrains Mono"',
                                      fontSize: "9px",
                                      letterSpacing: "0.16em",
                                      fontWeight: 600,
                                      padding: "2px 7px",
                                      borderRadius: "3px",
                                      background: "rgba(61, 214, 140, 0.1)",
                                      color: "rgb(61, 214, 140)",
                                      border:
                                        "1px solid rgba(61, 214, 140, 0.2)",
                                    }}
                                  >
                                    RET
                                  </span>
                                ) : (
                                  <span
                                    style={{
                                      fontFamily: '"JetBrains Mono"',
                                      fontSize: "9px",
                                      letterSpacing: "0.16em",
                                      fontWeight: 600,
                                      padding: "2px 7px",
                                      borderRadius: "3px",
                                      background: "rgba(255, 160, 80, 0.06)",
                                      color: "rgb(138, 122, 104)",
                                      border:
                                        "1px solid rgba(255, 160, 80, 0.08)",
                                    }}
                                  >
                                    PRES
                                  </span>
                                )}
                              </div>
                              <span
                                style={{
                                  textAlign: "right",
                                  fontFamily: '"JetBrains Mono"',
                                  fontSize: "11.5px",
                                  color: "rgb(90, 78, 66)",
                                  fontVariantNumeric: "tabular-nums",
                                }}
                              >
                                {formatCurrency(pisCofins)}
                              </span>
                              <span
                                style={{
                                  textAlign: "right",
                                  fontFamily: '"JetBrains Mono"',
                                  fontSize: "11.5px",
                                  color: "rgb(90, 78, 66)",
                                  fontVariantNumeric: "tabular-nums",
                                }}
                              >
                                {formatCurrency(csllIrpj)}
                              </span>
                              <span
                                style={{
                                  textAlign: "right",
                                  fontFamily: '"JetBrains Mono"',
                                  fontSize: "11.5px",
                                  color: "rgb(255, 194, 71)",
                                  fontVariantNumeric: "tabular-nums",
                                  fontWeight: 600,
                                }}
                              >
                                {formatCurrency(meta.irpj_adicional)}
                              </span>
                              <span
                                style={{
                                  textAlign: "right",
                                  fontFamily: '"JetBrains Mono"',
                                  fontSize: "11.5px",
                                  color: "rgb(61, 214, 140)",
                                  fontVariantNumeric: "tabular-nums",
                                  fontWeight: 600,
                                }}
                              >
                                {formatCurrency(ret)}
                              </span>

                              <div
                                style={{
                                  textAlign: "right",
                                  display: "flex",
                                  flexDirection: "column",
                                }}
                              >
                                <span
                                  style={{
                                    fontFamily: '"JetBrains Mono"',
                                    fontSize: "11.5px",
                                    fontWeight: 600,
                                    color: "rgb(240, 230, 216)",
                                    fontVariantNumeric: "tabular-nums",
                                  }}
                                >
                                  {formatCurrency(mesSoc)}
                                </span>
                                {isFiltered && (
                                  <span
                                    style={{
                                      fontFamily: '"JetBrains Mono"',
                                      fontSize: "9px",
                                      color: "rgb(90, 78, 66)",
                                      marginTop: "2px",
                                    }}
                                  >
                                    acum {formatCurrency(balSoc)}
                                  </span>
                                )}
                              </div>
                              <div
                                style={{
                                  textAlign: "right",
                                  display: "flex",
                                  flexDirection: "column",
                                }}
                              >
                                <span
                                  style={{
                                    fontFamily: '"JetBrains Mono"',
                                    fontSize: "11.5px",
                                    fontWeight: 600,
                                    color: "rgb(255, 122, 26)",
                                    fontVariantNumeric: "tabular-nums",
                                  }}
                                >
                                  {formatCurrency(mesFiscal)}
                                </span>
                                {isFiltered && (
                                  <span
                                    style={{
                                      fontFamily: '"JetBrains Mono"',
                                      fontSize: "9px",
                                      color: "rgb(90, 78, 66)",
                                      marginTop: "2px",
                                    }}
                                  >
                                    acum {formatCurrency(balFiscal)}
                                  </span>
                                )}
                              </div>

                              <div
                                style={{
                                  display: "flex",
                                  flexDirection: "column",
                                  alignItems: "center",
                                  gap: "3px",
                                }}
                              >
                                {isAntecipado && (
                                  <>
                                    <div
                                      style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "5px",
                                      }}
                                    >
                                      <span
                                        style={{
                                          width: "5px",
                                          height: "5px",
                                          borderRadius: "50%",
                                          background: "rgb(61, 214, 140)",
                                          boxShadow:
                                            "rgb(61, 214, 140) 0px 0px 6px",
                                        }}
                                      ></span>
                                      <span
                                        style={{
                                          fontFamily: '"JetBrains Mono"',
                                          fontSize: "9px",
                                          letterSpacing: "0.14em",
                                          color: "rgb(61, 214, 140)",
                                        }}
                                      >
                                        ANTECIPADO
                                      </span>
                                    </div>
                                    <span
                                      style={{
                                        fontFamily: '"JetBrains Mono"',
                                        fontSize: "9px",
                                        color: "rgb(90, 78, 66)",
                                        fontVariantNumeric: "tabular-nums",
                                      }}
                                    >
                                      {formatCurrency(Math.abs(statusDiff))}
                                    </span>
                                  </>
                                )}
                                {isDiferido && (
                                  <>
                                    <div
                                      style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "5px",
                                      }}
                                    >
                                      <span
                                        style={{
                                          width: "5px",
                                          height: "5px",
                                          borderRadius: "50%",
                                          background: "rgb(255, 194, 71)",
                                          boxShadow:
                                            "rgb(255, 194, 71) 0px 0px 6px",
                                        }}
                                      ></span>
                                      <span
                                        style={{
                                          fontFamily: '"JetBrains Mono"',
                                          fontSize: "9px",
                                          letterSpacing: "0.14em",
                                          color: "rgb(255, 194, 71)",
                                        }}
                                      >
                                        DIFERIDO PI
                                      </span>
                                    </div>
                                    <span
                                      style={{
                                        fontFamily: '"JetBrains Mono"',
                                        fontSize: "9px",
                                        color: "rgb(90, 78, 66)",
                                        fontVariantNumeric: "tabular-nums",
                                      }}
                                    >
                                      {formatCurrency(statusDiff)}
                                    </span>
                                  </>
                                )}
                                {!isAntecipado && !isDiferido && (
                                  <span
                                    style={{
                                      fontFamily: '"JetBrains Mono"',
                                      fontSize: "9px",
                                      color: "rgb(90, 78, 66)",
                                    }}
                                  >
                                    -
                                  </span>
                                )}
                              </div>
                            </button>

                            {expandedRow === idx &&
                              meta.unidades &&
                              meta.unidades.length > 0 && (
                                <div
                                  style={{
                                    background: "rgba(0, 0, 0, 0.3)",
                                    borderBottom:
                                      "1px solid rgba(255, 160, 80, 0.08)",
                                  }}
                                >
                                  <div
                                    style={{
                                      padding: "10px 18px",
                                      display: "grid",
                                      gridTemplateColumns:
                                        "120px minmax(200px, 1fr) 1fr 1fr 1fr 1fr 1fr 1fr",
                                      fontFamily: '"JetBrains Mono"',
                                      fontSize: "9px",
                                      letterSpacing: "0.18em",
                                      color: "rgb(90, 78, 66)",
                                    }}
                                  >
                                    <span>UNIDADE</span>
                                    <span>COMPRADOR</span>
                                    <span style={{ textAlign: "right" }}>
                                      VGV
                                    </span>
                                    <span style={{ textAlign: "right" }}>
                                      POC%
                                    </span>
                                    <span style={{ textAlign: "right" }}>
                                      REC. CAIXA
                                    </span>
                                    <span style={{ textAlign: "right" }}>
                                      TRIB. SOC.
                                    </span>
                                    <span style={{ textAlign: "right" }}>
                                      TRIB. FISCAL
                                    </span>
                                    <span style={{ textAlign: "right" }}>
                                      SALDO DIF.
                                    </span>
                                  </div>
                                  {meta.unidades.map((u, i) => {
                                    const sDiff =
                                      u.tributos_soc_acumulado -
                                      u.tributos_caixa_acumulado;
                                    const cxMes = isFiltered
                                      ? u.caixa_mes
                                      : u.caixa_acumulado;
                                    const tFisMes = isFiltered
                                      ? u.tributos_caixa_mes
                                      : u.tributos_caixa_acumulado;
                                    const tSocMes = isFiltered
                                      ? u.tributos_soc_mes
                                      : u.tributos_soc_acumulado;
                                    return (
                                      <div
                                        key={i}
                                        style={{
                                          padding: "8px 18px",
                                          display: "grid",
                                          gridTemplateColumns:
                                            "120px minmax(200px, 1fr) 1fr 1fr 1fr 1fr 1fr 1fr",
                                          fontFamily: '"JetBrains Mono"',
                                          fontSize: "10.5px",
                                          color: "rgb(138, 122, 104)",
                                          borderTop:
                                            "1px solid rgba(255, 160, 80, 0.03)",
                                          hover: {
                                            background:
                                              "rgba(255, 160, 80, 0.02)",
                                          },
                                        }}
                                      >
                                        <span
                                          style={{
                                            fontWeight: 600,
                                            color: "rgb(240, 230, 216)",
                                          }}
                                        >
                                          {u.unidade}
                                        </span>
                                        <span
                                          style={{
                                            overflow: "hidden",
                                            textOverflow: "ellipsis",
                                            whiteSpace: "nowrap",
                                          }}
                                        >
                                          {u.comprador}
                                        </span>
                                        <span
                                          style={{
                                            textAlign: "right",
                                            color: "#aa3333",
                                          }}
                                        >
                                          {formatCurrency(u.vgv)}
                                        </span>
                                        <span style={{ textAlign: "right" }}>
                                          {(meta.poc || 0).toFixed(2)}%
                                        </span>
                                        <span
                                          style={{
                                            textAlign: "right",
                                            color: "rgb(61, 214, 140)",
                                          }}
                                        >
                                          {formatCurrency(cxMes)}
                                        </span>
                                        <span
                                          style={{
                                            textAlign: "right",
                                            color: "rgb(240, 230, 216)",
                                          }}
                                        >
                                          {formatCurrency(tSocMes)}
                                        </span>
                                        <span
                                          style={{
                                            textAlign: "right",
                                            color: "rgb(255, 122, 26)",
                                          }}
                                        >
                                          {formatCurrency(tFisMes)}
                                        </span>
                                        <span
                                          style={{
                                            textAlign: "right",
                                            color:
                                              sDiff > 10
                                                ? "rgb(255, 194, 71)"
                                                : sDiff < -10
                                                  ? "rgb(61, 214, 140)"
                                                  : "inherit",
                                            fontWeight: 600,
                                          }}
                                        >
                                          {formatCurrency(sDiff)}
                                        </span>
                                      </div>
                                    );
                                  })}
                                </div>
                              )}
                          </React.Fragment>
                        );
                      })}
                      {filteredRows.length === 0 && (
                        <div
                          style={{
                            padding: "40px",
                            textAlign: "center",
                            fontFamily: '"JetBrains Mono"',
                            fontSize: "10px",
                            letterSpacing: "0.2em",
                            color: "rgb(90, 78, 66)",
                          }}
                        >
                          NENHUM DADO ENCONTRADO PARA OS FILTROS SELECIONADOS
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
