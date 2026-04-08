import sys, os
print("1. imports basicos OK")

import firebirdsql
print("2. firebirdsql OK")

import pdfplumber
print("3. pdfplumber OK")

try:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import google.generativeai as genai
    print("4. google.generativeai OK")
except Exception as e:
    print(f"4. google.generativeai ERRO: {e}")
    genai = None

import numpy as np
print("5. numpy OK")
import pandas as pd
print("6. pandas OK")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
_DOTENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_DOTENV_PATH, override=True)
print("7. dotenv OK")

if genai:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
    print("8. genai.configure OK")

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel as VertexModel, Part
    print("9. vertexai import OK - iniciando init...")
    vertexai.init(project="questor-explorer-prod", location="us-central1")
    print("9. vertexai.init OK")
except Exception as e:
    print(f"9. vertexai ERRO (ignorado): {e}")

print("10. TUDO OK - problema nao esta nos imports basicos")
