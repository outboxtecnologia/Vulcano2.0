import psycopg2

try:
    conn = psycopg2.connect("dbname=postgres user=postgres password=postgres host=localhost port=5432")
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print(cur.fetchone()[0])
    
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()
    print("PGVector Extension habilitada com sucesso!")
    
except Exception as e:
    print(f"Erro: {e}")
