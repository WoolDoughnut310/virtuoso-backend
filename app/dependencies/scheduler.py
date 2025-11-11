from fastapi import Depends
from typing import Annotated
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def get_scheduler():
    return scheduler

SchedulerDep = Annotated[AsyncIOScheduler, Depends(get_scheduler)]