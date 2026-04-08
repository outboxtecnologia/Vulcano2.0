import sys
import os
import traceback

# Add backend directory to module paths so we can import from main
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from main import api_contabilizacoes

def test_api():
    try:
        print("Iniciando requisição api_contabilizacoes (Mês: 6, Ano: 2025, Empresa: 959)...")
        # Podemos testar com empreendimento_id=None para varrer todos e ver qual quebra
        res = api_contabilizacoes(ano=2025, mes=6, empresa_id=959, empreendimento_id=None)
        print("Requisição bem-sucedida! Total de empreendimentos processados:", len(res.get("data", [])))
    except Exception as e:
        print("A API retornou erro ou sofreu crash!")
        traceback.print_exc()

if __name__ == "__main__":
    test_api()
