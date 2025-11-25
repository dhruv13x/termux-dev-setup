import pytest
import subprocess
from unittest.mock import patch, call
from termux_dev_setup.utils.banner import print_logo
from termux_dev_setup.utils.lock import process_lock
from termux_dev_setup.utils.shell import run_command, check_command
from termux_dev_setup.utils.status import info, success, error, warning, step

@patch('rich.console.Console.print')
def test_print_logo(mock_print):
    """
    Test that the print_logo function prints the logo.
    """
    print_logo()
    assert mock_print.call_count > 0

def test_process_lock():
    """
    Test that the process_lock context manager creates and removes a lock file.
    """
    with process_lock('test'):
        pass

@patch('fcntl.lockf')
def test_process_lock_already_locked(mock_lockf):
    """
    Test that the process_lock context manager exits when the lock is already held.
    """
    mock_lockf.side_effect = [IOError, None]  # First call raises IOError, second call in finally block does nothing
    with pytest.raises(SystemExit):
        with process_lock('test'):
            pass

@patch('subprocess.run')
def test_run_command(mock_run):
    """
    Test that the run_command function executes a command.
    """
    run_command('ls -l')
    mock_run.assert_called_once_with(['ls', '-l'], shell=False, check=True, text=True, capture_output=False)

@patch('subprocess.run')
def test_run_command_with_shell(mock_run):
    """
    Test that the run_command function executes a command with shell=True.
    """
    run_command('ls -l', shell=True)
    mock_run.assert_called_once_with('ls -l', shell=True, check=True, text=True, capture_output=False)

@patch('subprocess.run')
def test_run_command_capture_output(mock_run):
    """
    Test that the run_command function captures the output of a command.
    """
    run_command('ls -l', capture_output=True)
    mock_run.assert_called_once_with(['ls', '-l'], shell=False, check=True, text=True, capture_output=True)

@patch('subprocess.run')
def test_run_command_failure(mock_run):
    """
    Test that the run_command function raises an exception on command failure.
    """
    mock_run.side_effect = subprocess.CalledProcessError(1, 'ls -l', 'error')
    with pytest.raises(SystemExit):
        run_command('ls -l')

@patch('subprocess.run')
def test_run_command_file_not_found(mock_run):
    """
    Test that the run_command function raises an exception when the command is not found.
    """
    mock_run.side_effect = FileNotFoundError
    with pytest.raises(SystemExit):
        run_command('nonexistent_command')

@patch('shutil.which')
def test_check_command(mock_which):
    """
    Test that the check_command function returns True when a command exists.
    """
    mock_which.return_value = '/usr/bin/ls'
    assert check_command('ls')

@patch('shutil.which')
def test_check_command_not_found(mock_which):
    """
    Test that the check_command function returns False when a command does not exist.
    """
    mock_which.return_value = None
    assert not check_command('nonexistent_command')

@patch('rich.console.Console.print')
def test_info(mock_print):
    """
    Test that the info function prints an informational message.
    """
    info('test message')
    mock_print.assert_called_once_with('[info]ℹ[/info]  test message')

@patch('rich.console.Console.print')
def test_success(mock_print):
    """
    Test that the success function prints a success message.
    """
    success('test message')
    mock_print.assert_called_once_with('[success]✔[/success]  test message')

@patch('rich.console.Console.print')
def test_error(mock_print):
    """
    Test that the error function prints an error message and exits.
    """
    with pytest.raises(SystemExit):
        error('test message')
    mock_print.assert_called_once_with('[error]✖  test message[/error]')

@patch('rich.console.Console.print')
def test_warning(mock_print):
    """
    Test that the warning function prints a warning message.
    """
    warning('test message')
    mock_print.assert_called_once_with('[warning]⚠  test message[/warning]')

@patch('rich.console.Console.print')
def test_step(mock_print):
    """
    Test that the step function prints a step message.
    """
    step('test message')
    mock_print.assert_called_once_with('\n[step]== test message ==[/step]')
