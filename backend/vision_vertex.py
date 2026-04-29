import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
import base64
from core.agents.llm_provider import get_agent_llm

load_dotenv(".env")

image_path = r"C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\designs\vendas\Captura de tela 2026-04-28 073951.png"

with open(image_path, "rb") as image_file:
    image_data = base64.b64encode(image_file.read()).decode("utf-8")

llm = get_agent_llm()

message = HumanMessage(
    content=[
        {
            "type": "text",
            "text": "Você é um Especialista em React e TailwindCSS. O usuário reclamou que a tela recriada não estava 100% fiel à imagem. Gere O CÓDIGO REACT EXATO para reproduzi-la com precisão de pixels. \nRegras:\n1. Use as exatas mesmas cores, fontes, gaps e layout (sidebar, header, master-detail list).\n2. Inclua todo o Tailwind num grande componente único React chamado `export const VendasView = () => { ... }`.\n3. Coloque tudo dentro de ```jsx ... ```."
        },
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_data}"}
        }
    ]
)

print("Gerando código, aguarde...")
response = llm.invoke([message])

with open("vendas_generated_code.jsx", "w", encoding="utf-8") as f:
    f.write(response.content)

print("Código salvo em vendas_generated_code.jsx")
