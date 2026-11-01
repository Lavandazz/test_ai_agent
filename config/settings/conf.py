from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_KEY: str 
    API_DEEP_KEY: str
    MODEL: str

    class Config:
        env_file = ".env"

settings = Settings()
