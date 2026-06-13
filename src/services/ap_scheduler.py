from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup():
    await init_db()
    await sync_matches()
    scheduler.add_job(sync_matches, "cron", hour=3, minute=0)  # runs 3am daily
    scheduler.start()