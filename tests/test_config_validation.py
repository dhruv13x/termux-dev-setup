import os
import pytest
from unittest.mock import patch, mock_open
from termux_dev_setup.config import PostgresConfig, RedisConfig

class TestConfigValidation:

    # --- PostgresConfig Validation Tests ---

    def test_postgres_config_invalid_port_low(self):
        """Test that port < 1 raises ValueError."""
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            PostgresConfig(port=0)

    def test_postgres_config_invalid_port_high(self):
        """Test that port > 65535 raises ValueError."""
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            PostgresConfig(port=70000)

    def test_postgres_config_invalid_port_type(self):
        """Test that non-integer port raises ValueError."""
        # Note: Dataclasses don't enforce types on init, but we should check it in __post_init__ or validate
        # If passed as string "5432" it might be fine if we cast it, but "abc" should fail.
        # Since we are implementing validation, let's assume strictness or casting.
        with pytest.raises(ValueError, match="invalid literal for int"):
            PostgresConfig(port="abc") # type: ignore

    def test_postgres_config_empty_data_dir(self):
        """Test that empty data_dir raises ValueError."""
        with pytest.raises(ValueError, match="data_dir cannot be empty"):
            PostgresConfig(data_dir="")

    def test_postgres_config_empty_pg_user(self):
        """Test that empty pg_user raises ValueError."""
        with pytest.raises(ValueError, match="pg_user cannot be empty"):
            PostgresConfig(pg_user="")

    def test_postgres_env_override_validation(self):
        """Test validation applies when overriding from environment."""
        with patch.dict(os.environ, {"PG_DATA": ""}):
            with pytest.raises(ValueError, match="data_dir cannot be empty"):
                PostgresConfig()

    # --- RedisConfig Validation Tests ---

    def test_redis_config_invalid_port_env(self):
        """Test that invalid port in env raises ValueError."""
        with patch.dict(os.environ, {"REDIS_PORT": "99999"}):
            with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
                RedisConfig()

    def test_redis_config_invalid_port_type_env(self):
        """Test that non-integer port in env raises ValueError."""
        with patch.dict(os.environ, {"REDIS_PORT": "abc"}):
             # The current implementation raises ValueError from int(), but we might want a clearer message?
             # Or at least ensure it still raises ValueError.
             with pytest.raises(ValueError):
                RedisConfig()

    def test_redis_config_invalid_append_only(self):
        """Test that append_only must be 'yes' or 'no'."""
        with patch.dict(os.environ, {"APPENDONLY": "maybe"}):
            with pytest.raises(ValueError, match="append_only must be 'yes' or 'no'"):
                RedisConfig()

    def test_redis_config_empty_conf_path(self):
        """Test that conf_path cannot be empty."""
        with patch.dict(os.environ, {"REDIS_CONF": ""}):
            with pytest.raises(ValueError, match="conf_path cannot be empty"):
                RedisConfig()
