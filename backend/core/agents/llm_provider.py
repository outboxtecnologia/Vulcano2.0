import os

from gemini_auth_env import (
    resolve_google_application_credentials,
    vertex_credentials_configured,
    vertex_project_id,
    vertex_location,
)
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI

resolve_google_application_credentials()

try:
    import vertexai
    HAS_VERTEXAI = True
except ImportError:
    HAS_VERTEXAI = False

GEMINI_MODEL_ID = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def gemini_auth_available() -> bool:
    """True se Vertex (JSON montado) ou GEMINI_API_KEY estiver configurado."""
    if HAS_VERTEXAI and vertex_credentials_configured():
        return True
    return bool((os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip())


def get_agent_llm():
    """Retorna LLM LangChain ou None se IA não estiver configurada (app ainda sobe)."""
    if HAS_VERTEXAI and vertex_credentials_configured():
        # Quando Vertex está ativo, desligamos obrigatoriamente o thinking budget.
        # ATENÇÃO: model_kwargs é o canal correto — additional_kwargs NÃO chega ao
        # generation_config do Vertex e o CoT fica ativo (adiciona 20-60s/chamada).
        return ChatVertexAI(
            model_name=GEMINI_MODEL_ID,
            project=vertex_project_id(),
            location=vertex_location(),
            max_output_tokens=8192,
            model_kwargs={"thinking_config": {"thinking_budget": 0}},
        )
    api_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if not api_key:
        return None
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL_ID,
        max_output_tokens=8192,
        google_api_key=api_key,
    )
