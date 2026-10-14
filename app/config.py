from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""

    # Clef (Cloudflare Workers AI): segunda opinion con probabilidades, solo se usa en los scripts de evaluacion por ahora
    cloudflare_account_id: str = ""
    cloudflare_api_token: str = ""
    modelo_llm: str = "openai/gpt-oss-120b"

    # Datos de negocio (pedidos, incidencias), via SQLAlchemy
    database_url: str = "sqlite:///./triaje.db"

    # Cadena de conexion a pelo (sin +psycopg) para el checkpointer de LangGraph -- solo aplica con Postgres
    postgres_dsn: str = ""

    review_username: str = "admin"
    review_password: str = "cambia-esto"

    secret_key: str = "cambia-esto-en-produccion"


settings = Settings()
