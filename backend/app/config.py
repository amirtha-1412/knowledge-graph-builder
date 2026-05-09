from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()