from .utils.status import console, info, success, error, warning, step
from .config import PostgresConfig

class PostgresView:
    def print_status(self, is_running: bool, config: PostgresConfig):
        state = "[bold green]UP[/bold green]" if is_running else "[bold red]DOWN[/bold red]"
        console.print(f"  Status: {state}")
        console.print(f"  Data Dir: {config.data_dir}")
        console.print(f"  Log File: {config.log_file}")
        console.print(f"  Port: {config.port}")
        if is_running:
             console.print(f"  Connection: postgresql://{config.pg_user}:<PASS>@{config.host}:{config.port}/postgres")

    def print_step(self, message: str):
        step(message)

    def print_info(self, message: str):
        info(message)

    def print_success(self, message: str):
        success(message)

    def print_error(self, message: str, exit_code: int = 0):
        error(message, exit_code=exit_code)

    def print_warning(self, message: str):
        warning(message)
