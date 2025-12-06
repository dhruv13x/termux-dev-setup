from rich.prompt import Prompt, Confirm
from rich.console import Console
from .postgres import setup_postgres, manage_postgres
from .redis import setup_redis, manage_redis
from .otel import setup_otel, manage_otel
from .gcloud import setup_gcloud

console = Console()

def run_wizard():
    """Runs the interactive setup wizard."""
    console.print("\n[bold cyan]Interactive Setup Wizard[/bold cyan]")

    choices = [
        "postgres",
        "redis",
        "otel",
        "gcloud",
        "Exit"
    ]

    selected_service = Prompt.ask(
        "Which service would you like to set up?",
        choices=choices,
        default="Exit"
    )

    if selected_service == "Exit":
        return None

    return selected_service

def run_service_setup(service):
    """Runs the setup for the selected service."""
    if service == "postgres":
        if Confirm.ask("Do you want to proceed with PostgreSQL setup?"):
            setup_postgres()
    elif service == "redis":
        if Confirm.ask("Do you want to proceed with Redis setup?"):
            setup_redis()
    elif service == "otel":
        if Confirm.ask("Do you want to proceed with OpenTelemetry setup?"):
            setup_otel()
    elif service == "gcloud":
        if Confirm.ask("Do you want to proceed with Google Cloud CLI setup?"):
            setup_gcloud()
