import pytest
from unittest.mock import patch, MagicMock
from termux_dev_setup.postgres import setup_postgres
from pathlib import Path

@patch("termux_dev_setup.postgres.time.sleep")
@patch("termux_dev_setup.postgres.is_port_open")
@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command")
@patch("termux_dev_setup.postgres.Path")
@patch("termux_dev_setup.postgres.process_lock")
def test_setup_postgres_flow(
    mock_lock, mock_path, mock_check, mock_run, mock_is_port_open, mock_sleep
):
    # Mock Environment
    mock_check.return_value = True
    mock_is_port_open.side_effect = [False, True]  # Not running, then running

    # --- Mock Path for version detection ---
    mock_pg_lib = MagicMock()
    mock_ver_dir = MagicMock()
    mock_ver_dir.name = "16"
    mock_ver_dir.is_dir.return_value = True
    mock_pg_lib.iterdir.return_value = [mock_ver_dir]

    # This is the key fix: ensure the mocked path has a string representation
    # that contains the command name we're looking for.
    mock_bin_dir = MagicMock()
    mock_bin_dir.parent.name = "16"  # for the "Detected version" log message

    def bin_side_effect(arg):
        """Return a mock with a specific string representation based on the binary name."""
        m = MagicMock()
        m.__str__.return_value = f"/mock/path/to/{arg}"
        return m

    mock_bin_dir.__truediv__.side_effect = bin_side_effect
    mock_ver_dir.__truediv__.return_value = mock_bin_dir

    # --- Mock Path for data directory ---
    mock_data_dir = MagicMock()
    mock_pg_version_file = MagicMock()
    mock_pg_version_file.exists.return_value = False  # This will trigger initdb
    mock_data_dir.__truediv__.return_value = mock_pg_version_file

    def path_side_effect(arg):
        path_str = str(arg)
        if path_str == "/usr/lib/postgresql":
            return mock_pg_lib
        if path_str == "/var/lib/postgresql/data":
            return mock_data_dir
        # Return a default mock for other Path calls (e.g., log file dir)
        return MagicMock()

    mock_path.side_effect = path_side_effect

    # Run the setup
    setup_postgres()

    # Verify key steps were called
    # 1. apt update/install
    assert any("apt install" in str(call) for call in mock_run.call_args_list)

    # 2. initdb (since we mocked the data dir to not exist)
    # The command is wrapped in run_as_postgres -> runuser, but our string is in there.
    assert any("initdb" in str(call) for call in mock_run.call_args_list)

    # 3. Start command
    assert any(
        "pg_ctl" in str(call) and "start" in str(call)
        for call in mock_run.call_args_list
    )
