# Filesystem watcher

import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchers.events import SourceEvent, EventType

def _matches_exclusion(path: str, exclusions: list[str]) -> bool:
    # check if path matches any exclusion glob pattern or folder name.
    p = Path(path)
    parts = p.parts
    path_str = str(p)
    for pattern in exclusions:
        name = pattern.strip("*/")
        if not name:
            continue
        if "/" in name:
            if name in path_str:
                return True
        else:
            if name in parts:
                return True
    return False

class _Handler(FileSystemEventHandler):
    # Internal class that watchdog calls directly on filesystem events
    # Translate watchdog's own event objects into SourceEvent shape and pushes them onto an asyncio queue.

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop, exclusions: list[str]):
        self.queue = queue
        self.loop = loop
        self.exclusions = exclusions
    
    def _push(self, path: str, event_type: EventType):
        if _matches_exclusion(path, self.exclusions):
            return
        if Path(path).is_dir():
            return
        event = SourceEvent(path=path, event_type=event_type)
        self.loop.call_soon_threadsafe(self.queue.put_nowait, event)
    
    def on_created(self, event: FileSystemEvent):
        self._push(event.src_path, EventType.CREATED)
    
    def on_modified(self, event: FileSystemEvent):
        self._push(event.src_path, EventType.MODIFIED)

    def on_deleted(self, event: FileSystemEvent):
        self._push(event.src_path, EventType.DELETED)

class FilesystemWatcher:
    # Watches a list of dirs recursively and pushes SourceEvents onto an asyncio.Queue as file changes

    def __init__(self, watched_dirs: list[str], exclusions: list[str]):
        self.watched_dirs = watched_dirs
        self.exclusions = exclusions
        self.queue: asyncio.Queue = asyncio.Queue()
        self._observer = Observer()

    def start(self):
        loop = asyncio.get_event_loop()
        handler = _Handler(self.queue, loop, self.exclusions)
        for directory in self.watched_dirs:
            self._observer.schedule(handler, str(directory), recursive=True)
        self._observer.start()
    
    def stop(self):
        self._observer.stop()
        self._observer.join()
