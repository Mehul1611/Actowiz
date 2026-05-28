from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/rag"
    storage_path: str = "storage"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    chunk_size: int = 500
    chunk_overlap: int = 50
    allowed_extensions: set = {".pdf", ".md", ".txt", ".py", ".js", ".java"}

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
