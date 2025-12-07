import pytest
from unittest.mock import Mock, patch
from termux_dev_setup.views import PostgresView
from termux_dev_setup.config import PostgresConfig
from termux_dev_setup.errors import TDSError

@pytest.fixture
def mock_postgres_config():
    """Fixture to provide a mock PostgresConfig instance."""
    config = Mock(spec=PostgresConfig)
    config.data_dir = "/data/pg"
    config.log_file = "/log/pg.log"
    config.port = 5432
    config.pg_user = "testuser"
    config.host = "localhost"
    return config

@pytest.fixture
def postgres_view():
    """Fixture to provide a PostgresView instance."""
    return PostgresView()

@patch('termux_dev_setup.views.console')
def test_print_status_running(mock_console, postgres_view, mock_postgres_config):
    """Test print_status when PostgreSQL is running."""
    postgres_view.print_status(is_running=True, config=mock_postgres_config)
    mock_console.print.assert_any_call("  Status: [bold green]UP[/bold green]")
    mock_console.print.assert_any_call(f"  Data Dir: {mock_postgres_config.data_dir}")
    mock_console.print.assert_any_call(f"  Log File: {mock_postgres_config.log_file}")
    mock_console.print.assert_any_call(f"  Port: {mock_postgres_config.port}")
    mock_console.print.assert_any_call(f"  Connection: postgresql://{mock_postgres_config.pg_user}:<PASS>@{mock_postgres_config.host}:{mock_postgres_config.port}/postgres")

@patch('termux_dev_setup.views.console')
def test_print_status_down(mock_console, postgres_view, mock_postgres_config):
    """Test print_status when PostgreSQL is down."""
    postgres_view.print_status(is_running=False, config=mock_postgres_config)
    mock_console.print.assert_any_call("  Status: [bold red]DOWN[/bold red]")
    mock_console.print.assert_any_call(f"  Data Dir: {mock_postgres_config.data_dir}")
    mock_console.print.assert_any_call(f"  Log File: {mock_postgres_config.log_file}")
    mock_console.print.assert_any_call(f"  Port: {mock_postgres_config.port}")


@patch('termux_dev_setup.views.step')
def test_print_step(mock_step, postgres_view):
    """Test print_step method."""
    message = "Test step message"
    postgres_view.print_step(message)
    mock_step.assert_called_once_with(message)

@patch('termux_dev_setup.views.info')
def test_print_info(mock_info, postgres_view):
    """Test print_info method."""
    message = "Test info message"
    postgres_view.print_info(message)
    mock_info.assert_called_once_with(message)

@patch('termux_dev_setup.views.success')
def test_print_success(mock_success, postgres_view):
    """Test print_success method."""
    message = "Test success message"
    postgres_view.print_success(message)
    mock_success.assert_called_once_with(message)

@patch('termux_dev_setup.views.error')
def test_print_error_no_exit(mock_error, postgres_view):
    """Test print_error method with exit_code=0 (no exit)."""
    message = "Test error message"
    postgres_view.print_error(message, exit_code=0)
    mock_error.assert_called_once_with(message, exit_code=0)

@patch('termux_dev_setup.views.error', side_effect=TDSError("Test error"))
def test_print_error_with_exit(mock_error, postgres_view):
    """Test print_error method with exit_code=1 (should raise TDSError)."""
    message = "Test error message"
    with pytest.raises(TDSError):
        postgres_view.print_error(message, exit_code=1)
    mock_error.assert_called_once_with(message, exit_code=1)

@patch('termux_dev_setup.views.warning')
def test_print_warning(mock_warning, postgres_view):
    """Test print_warning method."""
    message = "Test warning message"
    postgres_view.print_warning(message)
    mock_warning.assert_called_once_with(message)
