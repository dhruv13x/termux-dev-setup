import pytest
from unittest.mock import patch, call
from termux_dev_setup.cli import main

@patch('termux_dev_setup.cli.print_logo')
def test_main_no_args(mock_print_logo):
    """
    Test that the main help message is printed when no arguments are provided.
    """
    with patch('sys.argv', ['tds']):
        with patch('argparse.ArgumentParser.print_help') as mock_print_help:
            main()
            mock_print_logo.assert_called_once()
            mock_print_help.assert_called_once()

@patch('termux_dev_setup.cli.setup_redis')
@patch('termux_dev_setup.cli.print_logo')
def test_setup_redis(mock_print_logo, mock_setup_redis):
    """
    Test the 'setup redis' command.
    """
    with patch('sys.argv', ['tds', 'setup', 'redis']):
        main()
        mock_print_logo.assert_called_once()
        mock_setup_redis.assert_called_once()

@patch('termux_dev_setup.cli.setup_otel')
@patch('termux_dev_setup.cli.print_logo')
def test_setup_otel(mock_print_logo, mock_setup_otel):
    """
    Test the 'setup otel' command.
    """
    with patch('sys.argv', ['tds', 'setup', 'otel']):
        main()
        mock_print_logo.assert_called_once()
        mock_setup_otel.assert_called_once()

@patch('termux_dev_setup.cli.print_logo')
def test_setup_no_service(mock_print_logo):
    """
    Test that the setup help message is printed when no service is provided.
    """
    with patch('sys.argv', ['tds', 'setup']):
        with patch('argparse.ArgumentParser.print_help') as mock_print_help:
            main()
            mock_print_logo.assert_called_once()
            mock_print_help.assert_called_once()

@patch('termux_dev_setup.cli.print_logo')
def test_setup_invalid_service(mock_print_logo):
    """
    Test that argparse exits when an invalid service is provided.
    """
    with patch('sys.argv', ['tds', 'setup', 'invalid']):
        with pytest.raises(SystemExit):
            main()
        mock_print_logo.assert_called_once()

@patch('termux_dev_setup.cli.manage_redis')
@patch('termux_dev_setup.cli.print_logo')
def test_manage_redis(mock_print_logo, mock_manage_redis):
    """
    Test the 'manage redis' command with different actions.
    """
    for action in ["start", "stop", "restart", "status"]:
        with patch('sys.argv', ['tds', 'manage', 'redis', action]):
            main()
            mock_manage_redis.assert_called_with(action)
    assert mock_print_logo.call_count == 4

@patch('termux_dev_setup.cli.print_logo')
def test_manage_no_service(mock_print_logo):
    """
    Test that the manage help message is printed when no service is provided.
    """
    with patch('sys.argv', ['tds', 'manage']):
        with patch('argparse.ArgumentParser.print_help') as mock_print_help:
            main()
            mock_print_logo.assert_called_once()
            mock_print_help.assert_called_once()


@patch('termux_dev_setup.cli.print_logo')
def test_manage_invalid_service(mock_print_logo):
    """
    Test that argparse exits when an invalid service is provided.
    """
    with patch('sys.argv', ['tds', 'manage', 'invalid', 'start']):
        with pytest.raises(SystemExit):
            main()
        mock_print_logo.assert_called_once()
