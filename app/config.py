from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""
    modelo_llm: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # SQLAlchemy: datos de negocio (pedidos, incidencias)
    database_url: str = "sqlite:///./triaje.db"

    # Cadena de conexion "pelada" para el checkpointer de LangGraph (solo Postgres)
    postgres_dsn: str = ""

    review_username: str = "admin"
    review_password: str = "cambia-esto"

    secret_key: str = "cambia-esto-en-produccion"


settings = Settings()
