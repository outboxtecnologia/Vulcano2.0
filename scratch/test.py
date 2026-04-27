import sys
import os
import fdb
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../backend")

def test_vulcano20():
    try:
        conn = fdb.connect(
            host="localhost",
            database=r"C:\Projetos\Vulcano2.0\DB\VULCANO.FDB",
            user="SYSDBA",
            password="masterkey",
            charset="WIN1252"
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM RECEBER")
        print("Conectado ao Vulcano 2.0 FDB! Total RECEBER:", cur.fetchone()[0])
        conn.close()
    except Exception as e:
        print("Erro ao conectar no Vulcano 2.0:", e)

if __name__ == "__main__":
    test_vulcano20()
