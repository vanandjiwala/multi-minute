from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import Session, select

from app.database import create_db, engine
from app.models.job import Job
from app.routers.scripts import router as scripts_router
from app.routers.jobs import router as jobs_router
from app.services.scheduler import scheduler, schedule_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    with Session(engine) as session:
        enabled_jobs = session.exec(select(Job).where(Job.enabled == True)).all()
        for job in enabled_jobs:
            schedule_job(job.id, job.cron_expression)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="multi-minute", lifespan=lifespan)

app.include_router(scripts_router)
app.include_router(jobs_router)


@app.get("/health")
def health():
    return {"status": "ok"}
