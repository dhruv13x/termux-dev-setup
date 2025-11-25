import os
import pytest
from unittest.mock import patch
from termux_dev_setup.otel import setup_otel

@patch('termux_dev_setup.otel.check_command', return_value=True)
@patch('termux_dev_setup.otel.run_command')
@patch('hashlib.sha256')
@patch.dict(os.environ, {
    'PREFIX': '/data/data/com.termux/files/usr',
    'OTEL_VERSION': '0.86.0',
    'OTEL_SHA256': '4416e167e6c033dbee89aeebeb8f8c0560d4518d31ecfe639100874f05bad984',
    'TERM': 'xterm'
})
def test_setup_otel_success(mock_sha256, mock_run_command, mock_check_command):
    """
    Test the successful installation of the OpenTelemetry Collector.
    """
    mock_sha256.return_value.hexdigest.return_value = '4416e167e6c033dbee89aeebeb8f8c0560d4518d31ecfe639100874f05bad984'
    with patch('pathlib.Path.exists', return_value=False):
        setup_otel()
    assert mock_run_command.call_count > 0

@patch('termux_dev_setup.otel.check_command', return_value=True)
@patch('termux_dev_setup.otel.run_command')
def test_setup_otel_already_done(mock_run_command, mock_check_command):
    """
    Test that the setup is skipped if the bootstrap flag is present.
    """
    with patch('pathlib.Path.exists', return_value=True):
        setup_otel()
    mock_run_command.assert_not_called()

@patch('termux_dev_setup.otel.check_command', return_value=False)
def test_setup_otel_no_apt(mock_check_command):
    """
    Test that the setup fails if apt is not found.
    """
    with pytest.raises(SystemExit):
        setup_otel()

@patch.dict(os.environ, {}, clear=True)
def test_setup_otel_missing_env_vars():
    """
    Test that the setup fails if environment variables are missing.
    """
    with patch('pathlib.Path.exists', return_value=False):
        with pytest.raises(SystemExit):
            setup_otel()

@patch('termux_dev_setup.otel.check_command', return_value=True)
@patch('termux_dev_setup.otel.run_command')
@patch('hashlib.sha256')
@patch.dict(os.environ, {
    'PREFIX': '/data/data/com.termux/files/usr',
    'OTEL_VERSION': '0.86.0',
    'OTEL_SHA256': '4416e167e6c033dbee89aeebeb8f8c0560d4518d31ecfe639100874f05bad984',
    'TERM': 'xterm',
    'OTEL_FORCE_UPDATE': '1'
})
def test_setup_otel_force_update(mock_sha256, mock_run_command, mock_check_command):
    """
    Test that the setup is forced when OTEL_FORCE_UPDATE is set.
    """
    mock_sha256.return_value.hexdigest.return_value = '4416e167e6c033dbee89aeebeb8f8c0560d4518d31ecfe639100874f05bad984'
    with patch('pathlib.Path.exists', return_value=True):
        setup_otel()
    assert mock_run_command.call_count > 0
