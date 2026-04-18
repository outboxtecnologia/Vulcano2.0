---
tags: [linguagem, stack, tech]
---
# 💻 Linguagens e Stack do Vulcano

A separação do nosso arsenal tecnológico que dá vida ao Questor Explorer e ao Vulcano:

### Backend
- **Python 3.12+**: Coração lógico e arquitetura orientada a serviços.
- **FastAPI**: Criação de rotas velozes e assíncronas (executa na porta 8000 via Uvicorn).
- **Relacional (Firebird)**: Onde residem os dados legados em `.fdb` do Questor e Vulcano.
- **Leve (SQLite)**: Persistência ágil de metadados, chunks vetoriais ou MOCs.

### Frontend
- **Framework (React + Vite)**: Escolhida pela velocidade de HMR (Hot Module Replacement) e arquitetura SPA (Single Page Application).  
  > *Por que não Next.js ou Vue?* O projeto foca em um painel interativo de alta densidade de dados (Client-Side Rendering intenso) focado em operações internas (não precisa de SEO ou SSR). Vite provê o bundle perfeito para a porta 5173.
- **Estilo (Vanilla CSS)**: Trabalhamos puramente com CSS Nativo e variáveis CSS (`var(--)`).  
  > *Por que não TailwindCSS?* Decisão de manter total controle sob a biblioteca estrita de Design System (tema "Tectonic Cyberpunk") sem o overhead de compilação utilitária, garantindo independência de ferramentas externas.
- **Comunicação Direta**: Sem uso de proxy. O Frontend consome as APIs do Backend velozmente através do FastAPI na porta local.

### Inteligência Artificial (IA)
- **Motor Primário**: Modelos da família Gemini via `Vertex AI` (`gemini-2.5-flash`), com autenticação via `Service Account JSON` de classe empresarial do Google Cloud para performance agressiva e contorno de rate limits.
- **Fallback**: Utilização de chaves de estúdio (API Key) via `Google AI Studio` se rodando em ambientes sem Service Accounts montadas.
- **Configuração de Orquestração**: Cadeias desenhadas com `LangGraph` para arquiteturas ReAct com uso zero do *thinking budget* nas instâncias de Vertex quando em extração JSON.
