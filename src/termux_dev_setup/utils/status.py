import sys
from rich.console import Console
from rich.theme import Theme

# Define a theme consistent with the bash scripts
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "step": "bold magenta",
})

console = Console(theme=custom_theme)

def info(msg: str) -> None:
    """Print an informational message."""
    console.print(f"[info]ℹ[/info]  {msg}")

def success(msg: str) -> None:
    """Print a success message."""
    console.print(f"[success]✔[/success]  {msg}")

def error(msg: str, exit_code: int = 1) -> None:
    """Print an error message and optionally exit."""
    console.print(f"[error]✖  {msg}[/error]")
    if exit_code != 0:
        sys.exit(exit_code)

def warning(msg: str) -> None:
    """Print a warning message."""
    console.print(f"[warning]⚠  {msg}[/warning]")

def step(msg: str) -> None:
    """Print a step/section header."""
    console.print(f"\n[step]== {msg} ==[/step]")
