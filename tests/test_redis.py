import pytest
from unittest.mock import patch, MagicMock, mock_open, call
from termux_dev_setup.redis import setup_redis
import subprocess

@patch("termux_dev_setup.redis.run_command")
@patch("termux_dev_setup.redis.check_command")
@patch("termux_dev_setup.redis.process_lock")
def test_setup_redis_flow(mock_lock, mock_check, mock_run):
    # Mock Environment
    # Default: commands exist
    mock_check.return_value = True
    
    # Configure run_command to return success for PONG check
    def run_side_effect(*args, **kwargs):
        # args[0] is the command string
        cmd = args[0]
        if "ping" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="PONG")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="")
        
    mock_run.side_effect = run_side_effect

    # Mock file operations using mock_open for the config file
    with patch("builtins.open", mock_open()) as mock_file:
        setup_redis()
        
        # Verify file write (config generation)
        mock_file.assert_called()
        handle = mock_file()
        handle.write.assert_called()
        
    # Verify APT install was called (since we mocked check_command to True, logic says "already installed")
    # Let's simulate "redis-server" NOT installed first to test installation path
    
    # Reset mocks
    mock_run.reset_mock()
    mock_check.side_effect = lambda cmd: cmd != "redis-server" # redis-server missing, others present
    
    with patch("builtins.open", mock_open()):
        setup_redis()
    
    assert any("apt install" in str(c) for c in mock_run.call_args_list)
