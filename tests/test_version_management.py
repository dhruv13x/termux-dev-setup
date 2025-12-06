import pytest
from unittest.mock import patch, MagicMock
from termux_dev_setup import cli, postgres

def test_setup_postgres_with_version():
    """Test that setup_postgres accepts and uses the version argument."""
    with patch("termux_dev_setup.postgres.PostgresInstaller.install_packages") as mock_install:
        with patch("termux_dev_setup.postgres.PostgresController.setup") as mock_setup:
             # We need to simulate the CLI parsing --version
             # But first let's verify postgres.setup_postgres can take a version arg
             # Currently it doesn't.

             # This test expects failure until we implement it.
             try:
                postgres.setup_postgres(version="15")
             except TypeError:
                pytest.fail("setup_postgres() got an unexpected keyword argument 'version'")

             # Verify that the version was passed down to the installer/controller
             # This part depends on how we implement it.
             # Let's assume we pass it to the installer.
             pass

def test_cli_version_flag():
    """Test that the CLI parser accepts --version."""
    with patch("termux_dev_setup.cli.setup_postgres") as mock_setup_pg:
        with patch("sys.argv", ["tds", "setup", "postgres", "--version", "15"]):
            cli.main()

        mock_setup_pg.assert_called_with(version="15")
