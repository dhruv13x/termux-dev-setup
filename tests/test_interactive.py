import pytest
from unittest.mock import patch, MagicMock
from termux_dev_setup import interactive, cli

# Fixtures mock_prompt and mock_confirm are now in conftest.py

def test_interactive_setup_wizard_selection(mock_prompt):
    """Test that the wizard asks for a service and returns the selection."""
    mock_prompt.return_value = "postgres"

    selected_service = interactive.run_wizard()

    mock_prompt.assert_called_once()
    assert selected_service == "postgres"

def test_interactive_setup_wizard_exit(mock_prompt):
    """Test that the wizard handles exit selection."""
    mock_prompt.return_value = "Exit"

    selected_service = interactive.run_wizard()

    assert selected_service is None

def test_cli_interactive_mode(mock_prompt, mock_confirm):
    """Test that the CLI invokes the interactive wizard when no args provided."""
    # We need to mock sys.argv or call the main function with appropriate args

    # Let's mock the interactive module functions
    with patch("termux_dev_setup.cli.interactive.run_wizard", return_value="postgres") as mock_wizard:
        with patch("termux_dev_setup.cli.interactive.run_service_setup") as mock_run_setup:

            # Simulate invoking the CLI with --interactive
            with patch("sys.argv", ["tds", "--interactive"]):
                cli.main()

            mock_wizard.assert_called_once()
            mock_run_setup.assert_called_with("postgres")

@pytest.mark.parametrize("service_name, setup_func_name", [
    ("postgres", "setup_postgres"),
    ("redis", "setup_redis"),
    ("otel", "setup_otel"),
    ("gcloud", "setup_gcloud"),
])
def test_run_service_setup_confirmed(service_name, setup_func_name, mock_confirm):
    """Test that selecting a service and confirming runs the setup."""
    mock_confirm.return_value = True

    with patch(f"termux_dev_setup.interactive.{setup_func_name}") as mock_setup:
        interactive.run_service_setup(service_name)
        mock_confirm.assert_called_once()
        mock_setup.assert_called_once()

@pytest.mark.parametrize("service_name, setup_func_name", [
    ("postgres", "setup_postgres"),
    ("redis", "setup_redis"),
    ("otel", "setup_otel"),
    ("gcloud", "setup_gcloud"),
])
def test_run_service_setup_declined(service_name, setup_func_name, mock_confirm):
    """Test that declining the setup does NOT run the setup."""
    mock_confirm.return_value = False

    with patch(f"termux_dev_setup.interactive.{setup_func_name}") as mock_setup:
        interactive.run_service_setup(service_name)
        mock_confirm.assert_called_once()
        mock_setup.assert_not_called()
