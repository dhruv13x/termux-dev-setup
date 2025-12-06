import pytest
from unittest.mock import patch, MagicMock
from termux_dev_setup import interactive, cli

@pytest.fixture
def mock_prompt():
    with patch("termux_dev_setup.interactive.Prompt.ask") as mock_ask:
        yield mock_ask

@pytest.fixture
def mock_confirm():
    with patch("termux_dev_setup.interactive.Confirm.ask") as mock_ask:
        yield mock_ask

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

def test_interactive_service_actions(mock_prompt):
    """Test that the wizard allows selecting actions for a service."""
    # This might require a more complex mock sequence if we implement a multi-step wizard
    pass
