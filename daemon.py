# RAGA daemon starts whole fookin thing

import asyncio
from config import WATCHED_DIRS, EXCLUSIONS
from ingestion.pipeline import run_pipeline
from watchers.filesystem import FilesystemWatcher

async def main():
    watcher = FilesystemWatcher(WATCHED_DIRS, EXCLUSIONS)
    watcher.start()
    print (f"Watching: {WATCHED_DIRS}")
    try:
        await run_pipeline(watcher.queue)
    finally:
        watcher.stop()

if __name__ == "__main__":
    asyncio.run(main())
    