"""Load settings from environment."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_audience: str = "authenticated"
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    gemini_api_key: str = ""  # For embeddings and text generation
    gemini_api_key_2: str = ""  # Backup key
    port: int = 8000
    
    # Ingestion settings
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    max_chunk_tokens: int = 700
    chunk_overlap_tokens: int = 100
    qdrant_collection: str = "document_chunks"
    
    # Retrieval settings
    retrieval_top_k: int = 8  # Number of chunks to retrieve (balanced for 2048 token limit)
    retrieval_min_score: float = 0.2
    
    # Generation settings
    max_output_tokens: int = 2048  # Maximum tokens for LLM response

    class Config:
        env_file = (".env", "../.env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
