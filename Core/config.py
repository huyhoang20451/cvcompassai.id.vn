from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    PAYOS_CLIENT_ID: str
    PAYOS_API_KEY: str
    PAYOS_CHECKSUM_KEY: str

    class Config:
        env_file = ".env"  # chỉ định file .env

# Khởi tạo settings global
settings = Settings()