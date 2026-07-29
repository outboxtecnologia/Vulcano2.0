import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=True)
import os
import asyncio
from typing import List

# Setup de banco
from sqlalchemy import create_engine, Column, String, Integer, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

# Setup API Vertex (semelhante ao main.py)
import vertexai
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
from google.oauth2 import service_account

PG_URL = os.environ.get("PG_VECTOR_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

engine = create_engine(PG_URL, echo=False)
Base = declarative_base()

class LctoEmbedding(Base):
    __tablename__ = 'erp_embeddings'
    id = Column(String, primary_key=True)       # ex: "Q_959_202505_12345" ou "V_959_202505_RX"
    fonte = Column(String)                      # "QUESTOR" ou "VULCANO"
    empresa_id = Column(Integer)
    ano_mes = Column(String)                    # "2025-05"
    texto_original = Column(Text)
    meta_dados = Column(JSONB)
    embedding = Vector(768)

def init_db():
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

# Singleton Vertex Embedding
_embed_model = None

def get_embed_model():
    global _embed_model
    if _embed_model is None:
        vc = os.environ.get("VERTEX_CREDENTIALS_JSON")
        if vc and os.path.exists(vc):
            credentials = service_account.Credentials.from_service_account_file(vc)
            pid = os.environ.get("VERTEX_PROJECT_ID", credentials.project_id)
            loc = os.environ.get("VERTEX_LOCATION", "us-central1")
            vertexai.init(project=pid, location=loc, credentials=credentials)
        else:
            # Fallback para default creds (gcloud auth)
            vertexai.init(location="us-central1")
        
        _embed_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    return _embed_model

async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Gera embeddings em lote para otimizar latência."""
    if not texts:
        return []
        
    model = get_embed_model()
    
    # Executa sincronicamente em uma thread isolada para n travar async loop
    def _run():
        inputs = [TextEmbeddingInput(t, "RETRIEVAL_DOCUMENT") for t in texts]
        responses = model.get_embeddings(inputs)
        return [r.values for r in responses]
    
    return await asyncio.to_thread(_run)

def save_embeddings(records: List[dict]):
    """Grava as matrizes geradas no PostgreSQL."""
    db = SessionLocal()
    try:
        for r in records:
            obj = LctoEmbedding(
                id=r["id"],
                fonte=r["fonte"],
                empresa_id=r["empresa_id"],
                ano_mes=r["ano_mes"],
                texto_original=r["texto_original"],
                meta_dados=r["meta_dados"],
                embedding=r["embedding"]
            )
            db.merge(obj) # Upsert
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
