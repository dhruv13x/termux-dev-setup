import pytest
from unittest.mock import patch, MagicMock, mock_open
from termux_dev_setup.redis import setup_redis
import subprocess


@patch("termux_dev_setup.redis.time.sleep")
@patch("termux_dev_setup.redis.run_command")
@patch("termux_dev_setup.redis.check_command")
@patch("termux_dev_setup.redis.Path")
@patch("termux_dev_setup.redis.process_lock")
def test_setup_redis_when_not_installed(
    mock_lock, mock_path, mock_check, mock_run, mock_sleep
):
    """
    Tests the full setup flow when redis-server is not initially installed.
    """
    # --- Mock Environment ---
    # 1. `check_command`: redis-server is missing, others (like runuser, adduser) are present.
    mock_check.side_effect = lambda cmd: cmd != "redis-server"

    # 2. `run_command` for the PING check to succeed after start
    def run_side_effect(*args, **kwargs):
        cmd = args[0]
        if "ping" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="PONG")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="")

    mock_run.side_effect = run_side_effect

    # 3. `Path`: The config file does NOT exist at first, but DOES exist after being written.
    mock_conf_path = MagicMock()
    # Call 1 (setup): check for backup -> False
    # Call 2 (manage->get_password): check for read -> True
    # Call 3 (manage->start): check for start -> True
    mock_conf_path.exists.side_effect = [False, True, True]
    mock_path.return_value = mock_conf_path

    # --- Run Test ---
    with patch("builtins.open", mock_open()) as mock_file:
        setup_redis()

        # --- Assertions ---
        # 1. Verify config file was written to. Use `assert_any_call` because the
        #    file is also opened for reading by `get_redis_password`.
        mock_file.assert_any_call(mock_conf_path, "w")
        handle = mock_file()
        assert "bind 127.0.0.1" in handle.write.call_args[0][0]

    # 2. Verify `apt install` was called because redis-server was missing
    assert any("apt install -y redis-server" in str(c) for c in mock_run.call_args_list)

    # 3. Verify the `redis-server` start command was issued
    assert any(
        "nohup redis-server" in str(c) and "&" in str(c) for c in mock_run.call_args_list
    )


@patch("termux_dev_setup.redis.time.sleep")
@patch("termux_dev_setup.redis.run_command")
@patch("termux_dev_setup.redis.check_command")
@patch("termux_dev_setup.redis.Path")
@patch("termux_dev_setup.redis.process_lock")
def test_setup_redis_when_already_installed(
    mock_lock, mock_path, mock_check, mock_run, mock_sleep
):
    """
    Tests the setup flow when redis-server is already installed.
    """
    # --- Mock Environment ---
    # 1. `check_command`: All commands exist
    mock_check.return_value = True

    # 2. `run_command` for PING
    def run_side_effect(*args, **kwargs):
        cmd = args[0]
        if "ping" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="PONG")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="")

    mock_run.side_effect = run_side_effect

    # 3. `Path` mock
    mock_conf_path = MagicMock()
    mock_conf_path.exists.side_effect = [False, True, True]
    mock_path.return_value = mock_conf_path

    # --- Run Test ---
    with patch("builtins.open", mock_open()) as mock_file:
        setup_redis()

        # --- Assertions ---
        # 1. Verify config file was written to
        mock_file.assert_any_call(mock_conf_path, "w")
        handle = mock_file()
        assert "bind 127.0.0.1" in handle.write.call_args[0][0]


    # 2. Verify `apt install` was NOT called
    assert not any("apt install" in str(c) for c in mock_run.call_args_list)

    # 3. Verify the start command was still issued
    assert any("nohup redis-server" in str(c) for c in mock_run.call_args_list)
