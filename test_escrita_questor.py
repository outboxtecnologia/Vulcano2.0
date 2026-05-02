import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from backend.core.services.questor_writer import inserir_lancamento_lctoger_teste

if __name__ == "__main__":
    print("Iniciando simulação de escrita no LCTOGER (Questor)...")
    payload = {
        "codigo_empresa": 959,
        "codigo_estab": 1,
        "data": "2026-05-02",
        "codigo_centro_custo": 35,
        "valor": 100.50,
        "historico": "Teste Insercao Vulcano via Script"
    }
    
    resultado = inserir_lancamento_lctoger_teste(payload)
    print("\n--- RESULTADO DA ESCRITA ---")
    print(resultado)
    print("----------------------------\n")
    if resultado.get("success"):
        print(f"Sucesso! O Generator avançou para o ID: {resultado.get('generated_id')}")
        print("Como o conn.commit() está comentado no código original, NENHUM DADO FOI REALMENTE SALVO NO BANCO ainda. Isso é apenas uma simulação segura para testar a comunicação com a escrita.")
    else:
        print("Falha na escrita. Verifique o erro acima.")
