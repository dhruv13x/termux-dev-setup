import pytest
from unittest.mock import patch, MagicMock
from termux_dev_setup.views import PostgresView
from termux_dev_setup.config import PostgresConfig

@pytest.fixture
def mock_console():
    with patch("termux_dev_setup.views.console") as mock:
        yield mock

@pytest.fixture
def mock_utils():
    with patch("termux_dev_setup.views.step") as mock_step, \
         patch("termux_dev_setup.views.info") as mock_info, \
         patch("termux_dev_setup.views.success") as mock_success, \
         patch("termux_dev_setup.views.error") as mock_error, \
         patch("termux_dev_setup.views.warning") as mock_warning:
        yield {
            "step": mock_step,
            "info": mock_info,
            "success": mock_success,
            "error": mock_error,
            "warning": mock_warning
        }

def test_print_status_up(mock_console):
    view = PostgresView()
    config = PostgresConfig()
    view.print_status(True, config)

    mock_console.print.assert_any_call("  Status: [bold green]UP[/bold green]")
    assert any("Connection: postgresql://" in str(call) for call in mock_console.print.call_args_list)

def test_print_status_down(mock_console):
    view = PostgresView()
    config = PostgresConfig()
    view.print_status(False, config)

    mock_console.print.assert_any_call("  Status: [bold red]DOWN[/bold red]")

def test_wrapper_methods(mock_utils):
    view = PostgresView()

    view.print_step("step msg")
    mock_utils["step"].assert_called_with("step msg")

    view.print_info("info msg")
    mock_utils["info"].assert_called_with("info msg")

    view.print_success("success msg")
    mock_utils["success"].assert_called_with("success msg")

    view.print_error("error msg", exit_code=1)
    mock_utils["error"].assert_called_with("error msg", exit_code=1)

    view.print_warning("warning msg")
    mock_utils["warning"].assert_called_with("warning msg")
