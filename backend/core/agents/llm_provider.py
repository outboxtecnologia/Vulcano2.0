import os
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI

HAS_VERTEXAI = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None
GEMINI_MODEL_ID = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

def get_agent_llm():
    if HAS_VERTEXAI:
        # Quando HAS_VERTEXAI é True, obrigatoriamente desligamos o thinking budget e usamos as credenciais nativas
        llm = ChatVertexAI(
            model_name=GEMINI_MODEL_ID,
            max_output_tokens=8192,
            additional_kwargs={"thinking_config": {"thinking_budget": 0}}
        )
    else:
        # Fallback caso local sem vertex
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL_ID,
            max_output_tokens=8192,
            google_api_key=os.environ.get("GEMINI_API_KEY")
        )
    return llm
