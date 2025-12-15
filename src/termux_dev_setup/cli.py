import argparse
import sys
from rich_argparse import RichHelpFormatter
from rich.console import Console
from .errors import TDSError
from .utils.banner import print_logo
from .postgres import setup_postgres, manage_postgres
from .redis import setup_redis, manage_redis
from .otel import setup_otel, manage_otel
from .gcloud import setup_gcloud
from . import interactive

console = Console()

def main():
    print_logo()
    parser = argparse.ArgumentParser(
        description="Termux Development Environment Setup Tool",
        formatter_class=RichHelpFormatter
    )

    # Add interactive flag to root parser
    parser.add_argument("--interactive", "-i", action="store_true", help="Run interactive setup wizard")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Setup Command ---
    setup_parser = subparsers.add_parser("setup", help="Install and configure services", formatter_class=RichHelpFormatter)
    setup_subparsers = setup_parser.add_subparsers(dest="service", help="Service to setup")

    # Postgres Setup
    pg_setup = setup_subparsers.add_parser("postgres", help="Install and configure PostgreSQL", formatter_class=RichHelpFormatter)
    pg_setup.add_argument("--version", help="Specify PostgreSQL version (e.g. 15)")

    # Redis Setup
    redis_setup = setup_subparsers.add_parser("redis", help="Install and configure Redis", formatter_class=RichHelpFormatter)
    redis_setup.add_argument("--version", help="Specify Redis version")

    # OpenTelemetry Setup
    otel_setup = setup_subparsers.add_parser("otel", help="Install OpenTelemetry Collector", formatter_class=RichHelpFormatter)
    otel_setup.add_argument("--version", help="Specify OpenTelemetry version")

    # GCloud Setup
    gcloud_setup = setup_subparsers.add_parser("gcloud", help="Install Google Cloud CLI", formatter_class=RichHelpFormatter)
    gcloud_setup.add_argument("--version", help="Specify GCloud version")

    # --- Manage Command ---
    manage_parser = subparsers.add_parser("manage", help="Start/Stop/Status services", formatter_class=RichHelpFormatter)
    manage_subparsers = manage_parser.add_subparsers(dest="service", help="Service to manage")

    # Manage Postgres
    pg_parser = manage_subparsers.add_parser("postgres", help="Manage PostgreSQL", formatter_class=RichHelpFormatter)
    pg_parser.add_argument("action", choices=["start", "stop", "restart", "status"], help="Action to perform")

    # Manage Redis
    redis_parser = manage_subparsers.add_parser("redis", help="Manage Redis", formatter_class=RichHelpFormatter)
    redis_parser.add_argument("action", choices=["start", "stop", "restart", "status"], help="Action to perform")

    # Manage OpenTelemetry
    otel_parser = manage_subparsers.add_parser("otel", help="Manage OpenTelemetry Collector", formatter_class=RichHelpFormatter)
    otel_parser.add_argument("action", choices=["start", "stop", "restart", "status"], help="Action to perform")

    args = parser.parse_args()

    try:
        if args.interactive:
            service = interactive.run_wizard()
            if service:
                interactive.run_service_setup(service)
            else:
                sys.exit(0)
        else:
            main_execution(args, setup_parser, manage_parser, parser)
    except TDSError as e:
        # Error is already printed if it came from error(), but if it came from elsewhere
        # we might want to ensure it's displayed. However, our convention is that TDSError
        # raised by error() has already been printed.
        # But if we raise TDSError manually, we should print it.
        # Let's assume error() handles printing. If we just raise TDSError elsewhere, we should print it.
        # For now, let's rely on error() being the main way to raise fatal errors.
        # But wait, we just changed error() to raise TDSError.
        # If we catch it here, we just need to exit.
        sys.exit(e.exit_code)
    except KeyboardInterrupt:
        console.print("\n[error]✖  Operation cancelled by user.[/error]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[error]✖  Unexpected error: {e}[/error]")
        sys.exit(1)

def main_execution(args, setup_parser, manage_parser, parser):
    if args.command == "setup":
        if args.service == "postgres":
            setup_postgres(version=args.version)
        elif args.service == "redis":
            setup_redis(version=args.version)
        elif args.service == "otel":
            setup_otel(version=args.version)
        elif args.service == "gcloud":
            setup_gcloud(version=args.version)
        else:
            setup_parser.print_help()

    elif args.command == "manage":
        if args.service == "postgres":
            manage_postgres(args.action)
        elif args.service == "redis":
            manage_redis(args.action)
        elif args.service == "otel":
            manage_otel(args.action)
        else:
            manage_parser.print_help()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
