from enum import Enum, auto
from dataclasses import dataclass

class ServiceStatus(Enum):
    RUNNING = auto()
    STOPPED = auto()
    STARTING = auto()
    STOPPING = auto()
    FAILED = auto()
    UNKNOWN = auto()
    ALREADY_RUNNING = auto()
    ALREADY_STOPPED = auto()
    MISSING_BINARIES = auto()
    TIMEOUT = auto()

@dataclass
class ServiceResult:
    status: ServiceStatus
    message: str = ""
