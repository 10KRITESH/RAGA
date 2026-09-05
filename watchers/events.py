# Shared data shape for filesystem events.

from dataclasses import dataclass
from enum import Enum

class EventType(str, Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"

@dataclass
class SourceEvent:
    path: str
    event_type: EventType
    source_type: str = "text"