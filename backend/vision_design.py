import os
from dotenv import load_dotenv
import google.generativeai as genai
import sys

# Carregar variáveis de ambiente
load_dotenv(".env")
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("Erro: GEMINI_API_KEY não encontrada.")
    sys.exit(1)

genai.configure(api_key=api_key)

image_path = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\designs\vendas\Captura de tela 2026-04-28 073951.png"

try:
    print("Uploading image...")
    sample_file = genai.upload_file(path=image_path, display_name="Design Vendas")
    print(f"Uploaded file '{sample_file.display_name}' as: {sample_file.uri}")

    model = genai.GenerativeModel('gemini-1.5-pro')
    prompt = """Você é um Engenheiro de Frontend Especialista.
Eu te enviei um mockup/screenshot de uma tela de Vendas de um ERP chamado Vulcano 2.0.
Descreva em MINÚCIAS:
1. Esquema de cores principal (fundo, cards, fontes, accents, gradients se houver).
2. O layout da tela (ex: sidebar, header, KPIs principais, tabelas, modais visíveis).
3. Efeitos de "vidro" (glassmorphism), bordas arredondadas e sombras.
4. Qual a estrutura de TailwindCSS recomendada para essa tela.
5. Se parecer haver animações (ex: barras de progresso, hover states, glows), liste-os."""

    response = model.generate_content([sample_file, prompt])
    print("\n--- ANÁLISE DE DESIGN ---")
    print(response.text)
    
except Exception as e:
    print(f"Erro: {e}")
