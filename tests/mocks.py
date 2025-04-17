import pytest
from unittest.mock import patch, MagicMock


# Mock Bittensor wallet to prevent initialization errors
@pytest.fixture(autouse=True)
def mock_bittensor_wallet():
    """Mock Bittensor wallet to prevent initialization errors."""
    with patch("bittensor.wallet.Wallet") as mock_wallet:
        mock_instance = MagicMock()
        mock_wallet.return_value = mock_instance
        mock_instance.coldkey = MagicMock()
        mock_instance.hotkey = MagicMock()
        mock_instance.coldkeypub = "mock_coldkeypub"
        mock_instance.hotkeypub = "mock_hotkeypub"
        yield mock_wallet


# Mock Redis client
@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis client to prevent connection errors."""
    with patch("app.services.redis_client") as mock_redis:
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        yield mock_redis


# Mock Subtensor
@pytest.fixture(autouse=True)
def mock_subtensor():
    """Mock Subtensor to prevent connection errors."""
    with patch("app.services.subtensor") as mock_subtensor:
        mock_subtensor.tao_dividends_per_hotkey.return_value = 100.0
        yield mock_subtensor


# Mock Celery task
@pytest.fixture(autouse=True)
def mock_celery_task():
    """Mock Celery task to prevent task execution errors."""
    with patch("app.worker.trigger_stake_task") as mock_task:
        mock_task.delay.return_value = MagicMock(id="mock_task_id")
        yield mock_task 