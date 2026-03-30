from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
    ]
    REQUEST_TIMEOUT: int = 30

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
