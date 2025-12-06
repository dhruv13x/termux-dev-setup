import pytest
from unittest.mock import patch

@pytest.fixture
def mock_prompt():
    with patch("termux_dev_setup.interactive.Prompt.ask") as mock_ask:
        yield mock_ask

@pytest.fixture
def mock_confirm():
    with patch("termux_dev_setup.interactive.Confirm.ask") as mock_ask:
        yield mock_ask
