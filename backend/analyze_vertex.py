import os
import sys
import asyncio
import base64

# Carrega ambiente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import main

async def analyze():
    image_path = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\designs\vendas\Captura de tela 2026-04-28 073951.png"
    
    with open(image_path, "rb") as f:
        img_data = f.read()

    # Como vertex está configurado no main.py, podemos usar o _gemini_generate_json_async?
    # Sim, mas vamos forçar a usar a classe VertexModel diretamente.
    
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    
    vertexai.init(project="questor-explorer-prod", location="us-central1")
    model = GenerativeModel("gemini-2.5-flash")
    
    prompt = """Você é um Especialista UX/UI. Analise este mockup da tela "Vendas" de um ERP (Vulcano 2.0).
    Forneça uma descrição detalhada de:
    - Paleta de cores (fundo principal, cards, acentos).
    - Elementos visuais (ex: KPIs, tabelas, estilo de bordas, se tem blur/glassmorphism).
    - Animações esperadas (ex: glow effects).
    
    Retorne em texto claro."""
    
    image_part = Part.from_data(mime_type="image/png", data=img_data)
    
    response = await model.generate_content_async([image_part, prompt])
    print("--- RESULTADO DA ANÁLISE VISUAL ---")
    print(response.text)

if __name__ == "__main__":
    asyncio.run(analyze())
