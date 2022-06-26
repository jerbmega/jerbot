from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

scheduler = AsyncIOScheduler()

scheduler.add_jobstore(SQLAlchemyJobStore(url="sqlite:///db/scheduler.db"), "default")
scheduler.start()
