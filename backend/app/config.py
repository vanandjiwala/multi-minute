from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    storage_path: str = "storage"
    db_path: str = "storage/scheduler.db"
    scripts_path: str = "storage/scripts"
    venvs_path: str = "storage/venvs"


settings = Settings()
