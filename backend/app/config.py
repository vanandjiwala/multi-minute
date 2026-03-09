from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    storage_path: str = "storage"
    db_path: str = "storage/scheduler.db"
    scripts_path: str = "storage/scripts"
    venvs_path: str = "storage/venvs"
    database_url: str = ""

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.db_path}"


settings = Settings()
