from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_URL: str
    DB_URL_ORIG: str

    class Config:
        env_file = '.env'


settings = Settings()