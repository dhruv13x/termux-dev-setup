import pytest
import subprocess
from unittest.mock import patch
from termux_dev_setup.utils.banner import print_logo
from termux_dev_setup.utils.lock import process_lock
from termux_dev_setup.utils.shell import run_command, check_command
from termux_dev_setup.utils.status import info, success, error, warning, step
from termux_dev_setup.errors import TDSError

# =================== banner.py Tests ===================
@patch('rich.console.Console.print')
def test_print_logo_renders(mock_print):
    """Test that print_logo calls the console print method multiple times."""
    print_logo()
    # 13 lines in logo string - 4 blank lines = 9 lines + 1 subtitle
    assert mock_print.call_count == 10

@patch('rich.console.Console.print')
def test_print_logo_with_fixed_palette_env(mock_print, monkeypatch):
    """Test that setting CREATE_DUMP_PALETTE uses a fixed palette."""
    monkeypatch.setenv("CREATE_DUMP_PALETTE", "1")
    print_logo()
    assert mock_print.call_count == 10

@patch('rich.console.Console.print')
def test_print_logo_with_invalid_palette_env(mock_print, monkeypatch):
    """Test that an invalid palette index falls back to procedural generation."""
    monkeypatch.setenv("CREATE_DUMP_PALETTE", "9999")
    print_logo()
    assert mock_print.call_count == 10

    monkeypatch.setenv("CREATE_DUMP_PALETTE", "not-a-number")
    print_logo()
    assert mock_print.call_count == 10 * 2


# =================== lock.py Tests ===================
def test_process_lock():
    with process_lock('test'):
        pass

@patch('fcntl.lockf')
def test_process_lock_already_locked(mock_lockf):
    """Test that the process_lock context manager exits when the lock is already held."""
    mock_lockf.side_effect = [IOError, None]  # First call raises IOError, second call in finally block does nothing
    with pytest.raises(TDSError):
        with process_lock('test'):
            pass


# =================== shell.py Tests ===================
@patch('subprocess.run')
def test_run_command(mock_run):
    run_command('ls -l')
    mock_run.assert_called_once_with(['ls', '-l'], shell=False, check=True, text=True, capture_output=False)

@patch('subprocess.run')
def test_run_command_with_shell(mock_run):
    run_command('ls -l', shell=True)
    mock_run.assert_called_once_with('ls -l', shell=True, check=True, text=True, capture_output=False)

@patch('subprocess.run')
def test_run_command_capture_output(mock_run):
    run_command('ls -l', capture_output=True)
    mock_run.assert_called_once_with(['ls', '-l'], shell=False, check=True, text=True, capture_output=True)

@patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'ls -l', 'error'))
def test_run_command_failure(mock_run):
    with pytest.raises(TDSError):
        run_command('ls -l')

@patch('subprocess.run', side_effect=FileNotFoundError)
def test_run_command_file_not_found(mock_run):
    with pytest.raises(TDSError):
        run_command('nonexistent_command')

@patch('shutil.which', return_value='/usr/bin/ls')
def test_check_command(mock_which):
    assert check_command('ls')

@patch('shutil.which', return_value=None)
def test_check_command_not_found(mock_which):
    assert not check_command('nonexistent_command')

# =================== status.py Tests ===================
@patch('rich.console.Console.print')
def test_info(mock_print):
    info('test message')
    mock_print.assert_called_once_with('[info]ℹ[/info]  test message')

@patch('rich.console.Console.print')
def test_success(mock_print):
    success('test message')
    mock_print.assert_called_once_with('[success]✔[/success]  test message')

@patch('rich.console.Console.print')
def test_error(mock_print):
    with pytest.raises(TDSError):
        error('test message')
    mock_print.assert_called_once_with('[error]✖  test message[/error]')

@patch('rich.console.Console.print')
def test_warning(mock_print):
    warning('test message')
    mock_print.assert_called_once_with('[warning]⚠  test message[/warning]')

@patch('rich.console.Console.print')
def test_step(mock_print):
    step('test message')
    mock_print.assert_called_once_with('\n[step]== test message ==[/step]')
