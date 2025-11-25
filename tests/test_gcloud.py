import pytest
from unittest.mock import patch, MagicMock, mock_open
from termux_dev_setup.gcloud import setup_gcloud

@patch("termux_dev_setup.gcloud.run_command")
@patch("termux_dev_setup.gcloud.check_command")
@patch("termux_dev_setup.gcloud.process_lock")
def test_setup_gcloud_flow(mock_lock, mock_check, mock_run):
    # Mock Environment
    mock_check.return_value = True
    
    # Mock file operations using mock_open for the repo file
    with patch("builtins.open", mock_open()) as mock_file:
        setup_gcloud()
        
        # Verify file write (repo generation)
        mock_file.assert_called()
        handle = mock_file()
        handle.write.assert_called()

    # Verify key steps
    assert any("curl" in str(c) for c in mock_run.call_args_list)
    assert any("apt-get install" in str(c) for c in mock_run.call_args_list)
    assert any("google-cloud-cli" in str(c) for c in mock_run.call_args_list)
