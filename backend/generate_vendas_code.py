import os
from dotenv import load_dotenv
import google.generativeai as genai
import sys

load_dotenv(".env")
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("Erro: GEMINI_API_KEY nao encontrada.")
    sys.exit(1)

genai.configure(api_key=api_key)

image_path = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\designs\vendas\Captura de tela 2026-04-28 073951.png"

try:
    print("Uploading image...")
    sample_file = genai.upload_file(path=image_path, display_name="Design Vendas Exact")
    
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    prompt = """Você é um Especialista em React e TailwindCSS.
Eu preciso que você olhe detalhadamente para este screenshot de design (um módulo de Vendas) e gere O CÓDIGO REACT EXATO para reproduzi-lo com precisão de pixels.

NÃO faça resumos. Apenas gere o código React (um único componente funcional grande) estilizado EXCLUSIVAMENTE com TailwindCSS.

Regras absolutas:
1. Use as exatas mesmas cores, bordas, padding, fontes e layouts. Se o fundo é preto (#000 ou #111), use isso. Se o botão é laranja brilhante, use o tom exato.
2. A estrutura de Sidebar (esquerda), Header, Lista de Vendas (Master) e Painel Direito (Detail) devem ser organizados com CSS Flexbox ou Grid usando Tailwind.
3. Use ícones Lucide React (ex: <Search />, <Plus />, <Filter />).
4. Crie mock de dados para preencher a lista e os detalhes exatamente como vistos na imagem.
5. Coloque todo o código dentro de um bloco markdown ```jsx ... ```.
6. A função principal deve ser: export const VendasView = ({ selectedEmpresa }) => { ... }
"""

    print("Gerando código, aguarde...")
    response = model.generate_content([sample_file, prompt])
    
    with open("vendas_generated_code.jsx", "w", encoding="utf-8") as f:
        f.write(response.text)
        
    print("Código salvo em vendas_generated_code.jsx")
    
except Exception as e:
    print(f"Erro: {e}")
