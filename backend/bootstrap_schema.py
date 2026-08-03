"""
Bootstrap único de estrutura de dados (SQLite + Firebird).

Uso:
  python bootstrap_schema.py --target all
  python bootstrap_schema.py --target sqlite
  python bootstrap_schema.py --target firebird
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys

try:
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError:
    load_dotenv = None


def _load_env() -> None:
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if load_dotenv is not None:
        load_dotenv(dotenv_path=dotenv_path, override=True)
        return

    # Fallback sem python-dotenv (útil quando rodar fora da venv).
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _sqlite_path() -> str:
    # Mantém compatível com o main.py
    if os.environ.get("POC_DATABASE_FILE"):
        return os.environ["POC_DATABASE_FILE"]
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "poc_database.sqlite")


def bootstrap_sqlite() -> None:
    db_path = _sqlite_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # main.py::init_sqlite
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS evolucao_obras (
            empreendimento TEXT,
            periodo TEXT,
            percentual REAL,
            PRIMARY KEY (empreendimento, periodo)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS import_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            target_table TEXT,
            mapping_json TEXT,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pdf_parser_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            python_code TEXT NOT NULL,
            sample_json TEXT,
            arquivo_gerado TEXT,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS empresa_parser_padrao (
            empresa_id INTEGER NOT NULL PRIMARY KEY,
            parser_template_id INTEGER NOT NULL,
            data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parser_template_id) REFERENCES pdf_parser_templates(id)
        )
        """
    )

    # init_baixas_db.py
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS operacoes_baixas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_receber INTEGER UNIQUE NOT NULL,
            empresa_id INTEGER NOT NULL,
            data_pagamento TEXT NOT NULL,
            valor_pago REAL NOT NULL,
            descontos REAL DEFAULT 0,
            acrescimos REAL DEFAULT 0,
            transacao_referencia TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # sync_projetadas.py — cache das parcelas em aberto (VENDAFORMAPAGTOPRAZO)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS parcelas_abertas_projetadas (
            prazo_id INTEGER PRIMARY KEY,
            data_venc TEXT,
            valor REAL,
            parcela_ref TEXT,
            forma_pagto_id INTEGER,
            venda_id INTEGER,
            cliente_id INTEGER,
            cliente_nome TEXT,
            unidade_descricao TEXT,
            empreendimento_id INTEGER
        )
        """
    )

    # create_sero_importacoes_table.py
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS SERO_IMPORTACOES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            competencia TEXT,
            cnpj_cpf TEXT,
            origem TEXT,
            valor_original REAL,
            taxa_correcao REAL,
            valor_atualizado REAL
        )
        """
    )

    # create_conversor_tables.py
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS conversor_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            import_mode TEXT,
            raw_pdf_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS conversor_data_staging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            comprador TEXT,
            cpf_cnpj TEXT,
            empreendimento TEXT,
            unidade TEXT,
            dt_vencimento DATE,
            dt_pagamento DATE,
            parcela TEXT,
            valor_raiz REAL,
            descontos REAL,
            acrescimos_variacoes REAL,
            total_pago REAL,
            FOREIGN KEY(batch_id) REFERENCES conversor_batches(id) ON DELETE CASCADE
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_batch ON conversor_data_staging(batch_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_empreend ON conversor_data_staging(empreendimento)")

    # main.py::_get_smart_importer_db
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS smart_importer_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            target_table TEXT NOT NULL,
            mapping_json TEXT NOT NULL,
            criado_em TEXT DEFAULT (datetime('now'))
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS smart_importer_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_hash TEXT UNIQUE NOT NULL,
            file_type TEXT NOT NULL,
            target_table TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDENTE',
            empresa_id_detectada INTEGER,
            cnpj_detectado TEXT,
            extracted_json TEXT,
            criado_em TEXT DEFAULT (datetime('now'))
        )
        """
    )

    conn.commit()
    conn.close()
    print(f"[OK] SQLite bootstrap finalizado em: {db_path}")


def bootstrap_firebird() -> None:
    try:
        import firebirdsql
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Dependência 'firebirdsql' não encontrada no Python atual. "
            "Use a venv do backend (./.venv/Scripts/python.exe) ou instale com "
            "'pip install -r requirements.txt'."
        ) from e

    db = os.environ.get("DB_PATH_VULCANO", "")
    if not db:
        raise RuntimeError("DB_PATH_VULCANO não configurado no .env")

    host = os.environ.get("FIREBIRD_HOST_VULCANO") or os.environ.get("FIREBIRD_HOST", "localhost")
    port = int(os.environ.get("FIREBIRD_PORT", "3050"))
    user = os.environ.get("FIREBIRD_USER", "SYSDBA")
    password = os.environ.get("FIREBIRD_PASSWORD", "masterkey")

    con = firebirdsql.connect(host=host, port=port, database=db, user=user, password=password, charset="WIN1252")
    cur = con.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM RDB$RELATIONS WHERE RDB$RELATION_NAME = 'POC_CUSTO_MENSAL_REAL' AND RDB$SYSTEM_FLAG = 0"
    )
    exists = int(cur.fetchone()[0]) > 0
    print(f"[INFO] Firebird tabela POC_CUSTO_MENSAL_REAL existe: {exists}")

    if not exists:
        cur.execute(
            """
            CREATE TABLE POC_CUSTO_MENSAL_REAL (
                ID                INTEGER NOT NULL,
                ID_EMPREENDIMENTO INTEGER NOT NULL,
                ANO               INTEGER NOT NULL,
                MES               INTEGER NOT NULL,
                COMPETENCIA       VARCHAR(10),
                CUSTO_TOTAL       DOUBLE PRECISION DEFAULT 0.0,
                CONSTRAINT PK_POC_CUSTO_MENSAL_REAL PRIMARY KEY (ID)
            )
            """
        )
        cur.execute("CREATE GENERATOR GEN_POC_CUSTO_MENSAL_REAL_ID")
        cur.execute(
            """
            CREATE TRIGGER TRG_POC_CUSTO_MENSAL_REAL_BI
            FOR POC_CUSTO_MENSAL_REAL
            ACTIVE BEFORE INSERT POSITION 0
            AS BEGIN
                IF (NEW.ID IS NULL) THEN
                    NEW.ID = GEN_ID(GEN_POC_CUSTO_MENSAL_REAL_ID, 1);
            END
            """
        )
        con.commit()
        print("[OK] Firebird: tabela/generator/trigger de POC_CUSTO_MENSAL_REAL criados.")
    con.close()


# DDL Postgres do banco operacional do app (APP_DB_KIND=postgres, database `vulcano2`).
# Fiel ao schema SQLite vivo; id_receber é TEXT (aceita 'prazo_<id>' das projetadas).
_APP_PG_DDL = """
CREATE TABLE IF NOT EXISTS sero_importacoes (
    id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    empresa_id int, competencia text, cnpj_cpf text, origem text,
    valor_original double precision, taxa_correcao double precision,
    valor_atualizado double precision
);
CREATE TABLE IF NOT EXISTS conversor_batches (
    id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    filename text NOT NULL, import_mode text, raw_pdf_text text,
    created_at timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS conversor_data_staging (
    id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    batch_id int NOT NULL REFERENCES conversor_batches(id) ON DELETE CASCADE,
    comprador text, cpf_cnpj text, empreendimento text, unidade text,
    dt_vencimento date, dt_pagamento date, parcela text,
    valor_raiz double precision, descontos double precision,
    acrescimos_variacoes double precision, total_pago double precision
);
CREATE INDEX IF NOT EXISTS idx_batch ON conversor_data_staging(batch_id);
CREATE INDEX IF NOT EXISTS idx_empreend ON conversor_data_staging(empreendimento);
CREATE TABLE IF NOT EXISTS cross_match_feedback (
    id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    created_at text DEFAULT (now()::text),
    empresa_id int, veredicto text, obs text, score_algoritmo double precision,
    q_conta int, q_historico text, q_valor double precision, q_data text, q_natureza text,
    v_conta int, v_historico text, v_valor double precision, v_data text, v_natureza text,
    q_tokens text, v_tokens text
);
CREATE TABLE IF NOT EXISTS cross_match_rules (
    id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    created_at text DEFAULT (now()::text),
    empresa_id int, rule_type text, q_conta int, v_conta int,
    confidence double precision, n_samples int, payload text
);
CREATE TABLE IF NOT EXISTS pdf_parser_templates (
    id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    nome text NOT NULL, descricao text, python_code text NOT NULL,
    sample_json text, arquivo_gerado text, data_criacao timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS empresa_parser_padrao (
    empresa_id int PRIMARY KEY,
    parser_template_id int NOT NULL REFERENCES pdf_parser_templates(id),
    data_atualizacao timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS evolucao_obras (
    empreendimento text, periodo text, percentual double precision,
    PRIMARY KEY (empreendimento, periodo)
);
CREATE TABLE IF NOT EXISTS import_templates (
    id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    nome text, target_table text, mapping_json text,
    data_criacao timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS operacoes_baixas (
    id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    id_receber text UNIQUE NOT NULL,
    empresa_id int NOT NULL,
    data_pagamento text NOT NULL,
    valor_pago double precision NOT NULL,
    descontos double precision DEFAULT 0,
    acrescimos double precision DEFAULT 0,
    transacao_referencia text,
    criado_em timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS parcelas_abertas_projetadas (
    prazo_id int PRIMARY KEY,
    data_venc text, valor double precision, parcela_ref text,
    forma_pagto_id int, venda_id int, cliente_id int,
    cliente_nome text, unidade_descricao text, empreendimento_id int
);
CREATE TABLE IF NOT EXISTS smart_importer_queue (
    id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    filename text NOT NULL, file_hash text UNIQUE NOT NULL,
    file_type text NOT NULL, target_table text NOT NULL,
    status text NOT NULL DEFAULT 'PENDENTE',
    empresa_id_detectada int, cnpj_detectado text, extracted_json text,
    criado_em text DEFAULT (now()::text)
);
CREATE TABLE IF NOT EXISTS smart_importer_templates (
    id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    nome text NOT NULL, target_table text NOT NULL, mapping_json text NOT NULL,
    criado_em text DEFAULT (now()::text)
);
CREATE TABLE IF NOT EXISTS usuarios_local (
    id int GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    usuario_id text UNIQUE NOT NULL,
    nome text, email text, senha text NOT NULL,
    tipo_permissao text DEFAULT 'ADMIN', ativo text DEFAULT 'T',
    criado_em timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS auditoria_memoria_arraste (
    chave_lancamento text PRIMARY KEY,
    conta_destino text, origem text, data_modificacao timestamptz
);
"""


def bootstrap_app_postgres() -> None:
    """Cria as tabelas operacionais do app no Postgres (APP_PG_DB, default vulcano2)."""
    import psycopg
    from db_app import _pg_conninfo
    info = _pg_conninfo()
    print(f"[INFO] Postgres app: {info['host']}:{info['port']}/{info['dbname']}")
    conn = psycopg.connect(**info)
    try:
        with conn.cursor() as cur:
            cur.execute(_APP_PG_DDL)
        conn.commit()
        print("[OK] Postgres: tabelas operacionais do app criadas/confirmadas.")
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap de schema SQLite/Firebird")
    parser.add_argument(
        "--target",
        choices=["all", "sqlite", "firebird", "app-pg"],
        default="all",
        help="Qual estrutura inicializar",
    )
    args = parser.parse_args()

    _load_env()
    try:
        if args.target == "app-pg":
            bootstrap_app_postgres()
        if args.target in ("all", "sqlite"):
            bootstrap_sqlite()
        if args.target in ("all", "firebird"):
            bootstrap_firebird()
        print("[DONE] Bootstrap concluído.")
        return 0
    except Exception as e:
        print(f"[ERRO] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
