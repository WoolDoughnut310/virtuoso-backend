from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    secret_key: str = "12345"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    db_user: str = "user"
    db_password: str = "password"
    db_host: str = "localhost"
    db_name: str = "mydb"
    db_port: int = 5432

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings()