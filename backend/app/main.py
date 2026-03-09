from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # scheduler start will go here
    yield
    # scheduler stop will go here


app = FastAPI(title="multi-minute", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}
