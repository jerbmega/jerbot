from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

scheduler = AsyncIOScheduler()

scheduler.configure(
    jobstores={"default": SQLAlchemyJobStore(url="sqlite:///db/scheduler.db")},
    job_defaults={"misfire_grace_time": None},
)
