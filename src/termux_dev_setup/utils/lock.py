import fcntl
from contextlib import contextmanager
from pathlib import Path
from .status import error

@contextmanager
def process_lock(name: str):
    """
    Ensure only one instance of a process (or critical section) is running.
    Creates a lock file in /tmp/tds_{name}.lock
    """
    lock_file_path = Path(f"/tmp/tds_{name}.lock")
    
    try:
        # Open for writing, create if not exists
        f = open(lock_file_path, 'w')
        
        # Try to acquire an exclusive lock without blocking
        fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        yield
        
    except IOError:
        # This block executes if the lock is already held
        error(f"Another instance of '{name}' is already running.", exit_code=1)
        
    finally:
        # We don't strictly need to unlock explicitly as closing the file handles it,
        # but it's good practice. We do NOT remove the file to avoid race conditions.
        if 'f' in locals():
            fcntl.lockf(f, fcntl.LOCK_UN)
            f.close()
