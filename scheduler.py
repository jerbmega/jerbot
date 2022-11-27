from apscheduler.schedulers.background import BackgroundScheduler

# I would much rather use AsyncIOScheduler but currently it appears to be bugged and nonfunctional, at least on my test setup.
# APScheduler 4 is being written right now and is designed for AsyncIO primarily, no sense in trying to debug the problem for a temporary setup, just use BackgroundScheduler for now.
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

scheduler = BackgroundScheduler()

scheduler.add_jobstore(SQLAlchemyJobStore(url="sqlite:///db/scheduler.db"), "default")
scheduler.configure(
    # APScheduler doesn't support just running a job if the bot had downtime, here's a nasty workaround! :kawaii: :compressed_torvalds: etc
    # This should be equivalent to the amount of seconds in a non-leap year... the bot ain't gonna be down for a year so this should be sufficient
    misfire_grace_time=31536000
)

scheduler.start()
