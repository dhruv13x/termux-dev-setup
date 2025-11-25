import pytest
from unittest.mock import patch, MagicMock
from termux_dev_setup.postgres import setup_postgres
from pathlib import Path

@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command")
@patch("termux_dev_setup.postgres.Path")
@patch("termux_dev_setup.postgres.process_lock")
def test_setup_postgres_flow(mock_lock, mock_path, mock_check, mock_run):
    # Mock Environment
    mock_check.return_value = True # assume all commands exist
    
    # Mock Path for version detection
    mock_pg_lib = MagicMock()
    mock_ver_dir = MagicMock()
    mock_ver_dir.name = "16"
    mock_ver_dir.is_dir.return_value = True
    
    # Setup the iterdir to return our version
    mock_pg_lib.iterdir.return_value = [mock_ver_dir]
    
    # When Path("/usr/lib/postgresql") is called, return our mock
    def side_effect(arg):
        if str(arg) == "/usr/lib/postgresql":
            return mock_pg_lib
        return MagicMock()
        
    mock_path.side_effect = side_effect

    # Run the setup
    setup_postgres()

    # Verify key steps were called
    # 1. apt update/install
    assert any("apt install" in str(call) for call in mock_run.call_args_list)
    
    # 2. initdb (if not exists)
    # We'd need to control .exists() on the data dir mock to test branches, 
    # but this confirms the function runs without crashing.
