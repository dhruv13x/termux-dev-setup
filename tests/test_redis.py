from unittest.mock import patch, mock_open
import pytest
import subprocess
from termux_dev_setup.redis import setup_redis, manage_redis

@patch('subprocess.run')
@patch('time.sleep', return_value=None)
@patch('pathlib.Path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open)
@patch('termux_dev_setup.redis.check_command', return_value=True)
def test_setup_redis_installed(mock_check_command, mock_open, mock_exists, mock_sleep, mock_run):
    """
    Test setup_redis when Redis is already installed.
    """
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout='PONG')
    setup_redis()
    assert mock_run.call_count > 0

@patch('subprocess.run')
@patch('time.sleep', return_value=None)
@patch('pathlib.Path.exists', return_value=False)
@patch('builtins.open', new_callable=mock_open)
@patch('termux_dev_setup.redis.check_command', return_value=False)
def test_setup_redis_not_installed(mock_check_command, mock_open, mock_exists, mock_sleep, mock_run):
    """
    Test setup_redis when Redis is not installed.
    """
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout='PONG')
    with patch('pathlib.Path.exists', return_value=True):
        setup_redis()
        assert mock_run.call_count > 0

@patch('subprocess.run')
@patch('time.sleep', return_value=None)
@patch('pathlib.Path.exists', return_value=True)
def test_manage_redis(mock_exists, mock_sleep, mock_run):
    """
    Test manage_redis with various actions.
    """
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout='PONG')
    for action in ['start', 'stop', 'restart', 'status']:
        manage_redis(action)
        assert mock_run.called

@patch('pathlib.Path.exists', return_value=False)
def test_manage_redis_no_config(mock_exists):
    """
    Test manage_redis when the config file does not exist.
    """
    with pytest.raises(SystemExit):
        manage_redis('start')
