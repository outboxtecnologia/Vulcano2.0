import sys
import os
import traceback

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from backend.main import get_conn

try:
    conn = get_conn("questor")
    print("Conexão OK!")
    conn.close()
except Exception as e:
    print(f"Erro de conexão: {e}")
    traceback.print_exc()
