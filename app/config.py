from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    ALLOWED_ORIGINS: list[str] = []
    CORS_ORIGIN_REGEX: str = ""
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    GOOGLE_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

print(f"--- DEBUG: Key being loaded is: [{settings.GOOGLE_API_KEY}] ---")
