import os
import sys
import firebirdsql

# Ponte Questor Firebird->Postgres (mesma usada em main.get_conn).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from db_pg import connect_questor_pg, questor_kind

# Obtém variáveis de ambiente comuns do Questor
DB_PATH_QUESTOR = os.environ.get("DB_PATH_QUESTOR", r"D:\Questor_Restore\Questor.fdb")
_fb = os.environ.get("FIREBIRD_HOST", "127.0.0.1")
FIREBIRD_HOST = os.environ.get("FIREBIRD_HOST_QUESTOR", _fb)
FIREBIRD_PORT = int(os.environ.get("FIREBIRD_PORT", "3050"))
FIREBIRD_USER = os.environ.get("FIREBIRD_USER", "SYSDBA")
FIREBIRD_PASSWORD = os.environ.get("FIREBIRD_PASSWORD", "masterkey")

def get_questor_write_conn():
    """
    Retorna uma conexão específica para ESCRITA no Questor.
    Postgres (QUESTOR_DB_KIND=postgres) ou Firebird, conforme o backend ativo.
    """
    if questor_kind() == "postgres":
        return connect_questor_pg()
    return firebirdsql.connect(
        host=FIREBIRD_HOST,
        port=FIREBIRD_PORT,
        database=DB_PATH_QUESTOR,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASSWORD,
        charset='WIN1252',
        # Configuração recomendada para read_committed no Firebird
        isolation_level=firebirdsql.ISOLATION_LEVEL_READ_COMMITED_RO
    )

def get_next_generator_id(conn, generator_name: str) -> int:
    """
    Obtém o próximo ID seguro gerado pelo banco para a entidade solicitada,
    evitando colisões e corrupção de concorrência.

    NOTA (migração PG): no Postgres o Questor usa sequences (`nextval`) OU triggers
    BEFORE INSERT que já atribuem a chave — nesse caso NÃO chame esta função, deixe o
    trigger gerar. O nome da sequence no PG pode diferir do generator Firebird; confirmar
    no banco antes de ativar escrita manual de ID.
    """
    cur = conn.cursor()
    try:
        if getattr(conn, "kind", "firebird") == "postgres":
            cur.execute("SELECT nextval(?)", (generator_name,))
        else:
            # A sintaxe GEN_ID avança a sequence no momento da execução
            cur.execute(f"SELECT GEN_ID({generator_name}, 1) FROM RDB$DATABASE")
        row = cur.fetchone()
        if not row or row[0] is None:
            raise Exception(f"Falha ao obter ID do generator {generator_name}")
        return int(row[0])
    finally:
        cur.close()

def inserir_lancamento_lctoger_teste(dados_lancamento: dict) -> dict:
    """
    EXEMPLO/TEMPLATE: Insere um registro no LCTOGER de forma segura.
    Espera um dict com as chaves necessárias.
    """
    conn = firebirdsql.connect(
        host=FIREBIRD_HOST,
        port=FIREBIRD_PORT,
        database=DB_PATH_QUESTOR,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASSWORD,
        charset='WIN1252'
    )
    
    try:
        cur = conn.cursor()
        
        # 1. Pega ID da sequencia
        novo_id = get_next_generator_id(conn, "GEN_LCTOGER_ID")
        
        # 2. Prepara dados. No Questor real, LCTOGER tem MUITOS campos obrigatórios.
        # Estamos simplificando com os chaves.
        # TODO: Adaptar aos campos not null da versão específica do cliente
        
        empresa = dados_lancamento.get("codigo_empresa", 959)
        filial = dados_lancamento.get("codigo_estab", 1)
        data_lcto = dados_lancamento.get("data")
        cc = dados_lancamento.get("codigo_centro_custo")
        valor = float(dados_lancamento.get("valor", 0.0))
        historico = dados_lancamento.get("historico", "Lançamento via API")
        
        sql = """
            INSERT INTO LCTOGER (
                ID, CODIGOEMPRESA, CODIGOESTAB, DATALCTO, VALORLCTO, HISTORICO, CODIGOCENTROCUSTO
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (novo_id, empresa, filial, data_lcto, valor, historico, cc)
        
        # cur.execute(sql, params)
        # conn.commit()
        
        # ATENÇÃO: Deixamos COMENTADO a execução real até o usuário confirmar 
        # que o schema da tabela local aceita este insert simplificado sem estourar NOT NULLs.
        
        return {
            "success": True, 
            "message": f"Simulação concluída. Novo ID gerado: {novo_id}",
            "generated_id": novo_id
        }
        
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
