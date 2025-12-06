class TDSError(Exception):
    """Base exception for Termux Dev Setup errors."""
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code

class ServiceError(TDSError):
    """Raised when a service operation fails."""
    pass

class ConfigError(TDSError):
    """Raised when configuration is invalid."""
    pass
