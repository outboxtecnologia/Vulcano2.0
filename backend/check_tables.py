"""
Verifica e cria a tabela POC_CUSTO_MENSAL_REAL no banco Vulcano se não existir.
"""
import fdb
import sys
import os
from dotenv import load_dotenv

# Carrega backend/.env para evitar path fixo em código.
_dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_dotenv_path, override=True)

db = os.environ.get(
    "DB_PATH_VULCANO",
    r'C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\Vulcano 2025\VULCANO 2025.fdb'
)
host = os.environ.get("FIREBIRD_HOST_VULCANO") or os.environ.get("FIREBIRD_HOST", "localhost")
port = int(os.environ.get("FIREBIRD_PORT", "3050"))
user = os.environ.get("FIREBIRD_USER", "SYSDBA")
password = os.environ.get("FIREBIRD_PASSWORD", "masterkey")

try:
    con = fdb.connect(host=host, port=port, database=db, user=user, password=password, charset='WIN1252')
except Exception as e:
    print(f"ERRO ao conectar: {e}")
    sys.exit(1)

cur = con.cursor()

# Verifica se a tabela existe
cur.execute("SELECT COUNT(*) FROM RDB$RELATIONS WHERE RDB$RELATION_NAME = 'POC_CUSTO_MENSAL_REAL' AND RDB$SYSTEM_FLAG = 0")
exists = cur.fetchone()[0]
print(f"Tabela POC_CUSTO_MENSAL_REAL existe: {bool(exists)}")

if not exists:
    print("Criando tabela...")
    try:
        cur.execute("""
            CREATE TABLE POC_CUSTO_MENSAL_REAL (
                ID              INTEGER NOT NULL,
                ID_EMPREENDIMENTO INTEGER NOT NULL,
                ANO             INTEGER NOT NULL,
                MES             INTEGER NOT NULL,
                COMPETENCIA     VARCHAR(10),
                CUSTO_TOTAL     DOUBLE PRECISION DEFAULT 0.0,
                CONSTRAINT PK_POC_CUSTO_MENSAL_REAL PRIMARY KEY (ID)
            )
        """)
        cur.execute("""
            CREATE GENERATOR GEN_POC_CUSTO_MENSAL_REAL_ID
        """)
        cur.execute("""
            CREATE TRIGGER TRG_POC_CUSTO_MENSAL_REAL_BI
            FOR POC_CUSTO_MENSAL_REAL
            ACTIVE BEFORE INSERT POSITION 0
            AS BEGIN
                IF (NEW.ID IS NULL) THEN
                    NEW.ID = GEN_ID(GEN_POC_CUSTO_MENSAL_REAL_ID, 1);
            END
        """)
        con.commit()
        print("Tabela criada com sucesso!")
    except Exception as e:
        con.rollback()
        print(f"ERRO ao criar: {e}")
        sys.exit(1)

# Lista todas as tabelas POC_
cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY 1")
print("\nTabelas POC/CUSTO no banco:")
for r in cur.fetchall():
    name = r[0].decode('win1252').strip() if isinstance(r[0], bytes) else str(r[0]).strip()
    if 'POC' in name.upper() or 'CUSTO' in name.upper():
        print(f"  {name}")

con.close()
print("\nOK")
