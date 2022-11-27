from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

scheduler = AsyncIOScheduler()

scheduler.add_jobstore(SQLAlchemyJobStore(url="sqlite:///db/scheduler.db"), "default")
scheduler.configure(
    # APScheduler doesn't support just running a job if the bot had downtime, here's a nasty workaround! :kawaii: :compressed_torvalds: etc
    # This should be equivalent to the amount of seconds in a non-leap year... the bot ain't gonna be down for a year so this should be sufficient
    misfire_grace_time=31536000
)
