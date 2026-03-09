from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

connect_args = {}
if settings.effective_database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.effective_database_url, connect_args=connect_args)


def create_db():
    if settings.effective_database_url.startswith("sqlite"):
        Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
