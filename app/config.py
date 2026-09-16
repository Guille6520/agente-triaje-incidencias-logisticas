from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""
    modelo_llm: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # Datos de negocio (pedidos, incidencias), via SQLAlchemy
    database_url: str = "sqlite:///./triaje.db"

    # Cadena de conexion a pelo (sin +psycopg) para el checkpointer de LangGraph -- solo aplica con Postgres
    postgres_dsn: str = ""

    review_username: str = "admin"
    review_password: str = "cambia-esto"

    secret_key: str = "cambia-esto-en-produccion"


settings = Settings()
