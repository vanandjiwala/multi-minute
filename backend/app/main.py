from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import create_db
from app.routers.scripts import router as scripts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    # scheduler start will go here
    yield
    # scheduler stop will go here


app = FastAPI(title="multi-minute", lifespan=lifespan)

app.include_router(scripts_router)


@app.get("/health")
def health():
    return {"status": "ok"}
