from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

engine = create_engine(f"sqlite:///{settings.db_path}")


def create_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
