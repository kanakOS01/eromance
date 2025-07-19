from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_URL: str
    DB_URL_ORIG: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    REDIRECT_URL: str
    FRONTEND_URL: str
    ALGORITHM: str = 'HS256'

    class Config:
        env_file = '.env'


settings = Settings()