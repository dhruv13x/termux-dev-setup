import pytest
from unittest.mock import patch, MagicMock
from termux_dev_setup.cli import main

# =================== Mocks for all dispatched functions ===================
@pytest.fixture(autouse=True)
def mock_commands(monkeypatch):
    """Auto-mock all functions that the CLI can call."""
    monkeypatch.setattr("termux_dev_setup.cli.setup_postgres", MagicMock())
    monkeypatch.setattr("termux_dev_setup.cli.manage_postgres", MagicMock())
    monkeypatch.setattr("termux_dev_setup.cli.setup_redis", MagicMock())
    monkeypatch.setattr("termux_dev_setup.cli.manage_redis", MagicMock())
    monkeypatch.setattr("termux_dev_setup.cli.setup_otel", MagicMock())
    monkeypatch.setattr("termux_dev_setup.cli.setup_gcloud", MagicMock())
    monkeypatch.setattr("termux_dev_setup.cli.print_logo", MagicMock())

# =================== Help and No-Command Tests ===================
def test_main_no_args():
    with patch('sys.argv', ['tds']), \
         patch('argparse.ArgumentParser.print_help') as mock_print_help:
        main()
        mock_print_help.assert_called_once()

def test_setup_no_service():
    with patch('sys.argv', ['tds', 'setup']), \
         patch('argparse.ArgumentParser.print_help') as mock_print_help:
        main()
        mock_print_help.assert_called_once()

def test_manage_no_service():
    with patch('sys.argv', ['tds', 'manage']), \
         patch('argparse.ArgumentParser.print_help') as mock_print_help:
        main()
        mock_print_help.assert_called_once()

# =================== Setup Command Tests ===================
@pytest.mark.parametrize("service, mock_target", [
    ("postgres", "termux_dev_setup.cli.setup_postgres"),
    ("redis", "termux_dev_setup.cli.setup_redis"),
    ("otel", "termux_dev_setup.cli.setup_otel"),
    ("gcloud", "termux_dev_setup.cli.setup_gcloud"),
])
def test_setup_commands(service, mock_target):
    with patch(mock_target) as mock_func:
        with patch('sys.argv', ['tds', 'setup', service]):
            main()
            mock_func.assert_called_once()

# =================== Manage Command Tests ===================
@pytest.mark.parametrize("action", ["start", "stop", "restart", "status"])
def test_manage_postgres_commands(action):
    from termux_dev_setup.cli import manage_postgres
    with patch('sys.argv', ['tds', 'manage', 'postgres', action]):
        main()
        manage_postgres.assert_called_with(action)

@pytest.mark.parametrize("action", ["start", "stop", "restart", "status"])
def test_manage_redis_commands(action):
    from termux_dev_setup.cli import manage_redis
    with patch('sys.argv', ['tds', 'manage', 'redis', action]):
        main()
        manage_redis.assert_called_with(action)

# =================== Exception Handling Tests ===================
def test_keyboard_interrupt():
    from termux_dev_setup.cli import setup_postgres
    setup_postgres.side_effect = KeyboardInterrupt
    with patch('sys.argv', ['tds', 'setup', 'postgres']), \
         patch('rich.console.Console.print') as mock_print:
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 130
        mock_print.assert_called_with("\n[error]✖  Operation cancelled by user.[/error]")

def test_generic_exception():
    from termux_dev_setup.cli import setup_gcloud
    setup_gcloud.side_effect = Exception("Something broke")
    with patch('sys.argv', ['tds', 'setup', 'gcloud']), \
         patch('rich.console.Console.print') as mock_print:
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        mock_print.assert_called_with("[error]✖  Unexpected error: Something broke[/error]")
