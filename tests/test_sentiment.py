import pytest
from unittest.mock import patch, MagicMock
import os


@pytest.mark.asyncio
async def test_get_sentiment_success(client, db_session):
    """Test successful sentiment analysis."""
    api_key = os.getenv("API_TOKEN", "test_key")
    
    # Mock all external services
    with patch("app.services.redis_client") as mock_redis, \
         patch("app.utils.Subtensor") as mock_subtensor, \
         patch("app.utils.get_sentiment") as mock_get_sentiment:
        
        mock_redis.get.return_value = None
        mock_instance = MagicMock()
        mock_subtensor.return_value = mock_instance
        mock_instance.get_tao_dividends.return_value = {"test_hotkey": 100.0}
        mock_get_sentiment.return_value = 0.8
        
        response = client.get(
            "/api/v1/tao_dividends?netuid=18&hotkey=test_hotkey&trade=false",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "dividends" in data
        assert "hotkey" in data
        assert "netuid" in data
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_get_sentiment_failure(client, db_session):
    """Test failed sentiment analysis."""
    api_key = os.getenv("API_TOKEN", "test_key")
    
    # Mock all external services
    with patch("app.services.redis_client") as mock_redis, \
         patch("app.utils.Subtensor") as mock_subtensor, \
         patch("app.utils.get_sentiment") as mock_get_sentiment:
        
        mock_redis.get.return_value = None
        mock_instance = MagicMock()
        mock_subtensor.return_value = mock_instance
        mock_instance.get_tao_dividends.return_value = {"test_hotkey": 100.0}
        mock_get_sentiment.return_value = -0.8
        
        response = client.get(
            "/api/v1/tao_dividends?netuid=18&hotkey=test_hotkey&trade=false",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "dividends" in data
        assert "hotkey" in data
        assert "netuid" in data
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_get_sentiment_neutral(client, db_session):
    """Test neutral sentiment analysis."""
    api_key = os.getenv("API_TOKEN", "test_key")
    
    # Mock all external services
    with patch("app.services.redis_client") as mock_redis, \
         patch("app.utils.Subtensor") as mock_subtensor, \
         patch("app.utils.get_sentiment") as mock_get_sentiment:
        
        mock_redis.get.return_value = None
        mock_instance = MagicMock()
        mock_subtensor.return_value = mock_instance
        mock_instance.get_tao_dividends.return_value = {"test_hotkey": 100.0}
        mock_get_sentiment.return_value = 0.0
        
        response = client.get(
            "/api/v1/tao_dividends?netuid=18&hotkey=test_hotkey&trade=false",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "dividends" in data
        assert "hotkey" in data
        assert "netuid" in data
        assert "timestamp" in data
