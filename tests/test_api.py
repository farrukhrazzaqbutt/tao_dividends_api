import pytest
from unittest.mock import patch, MagicMock
from app.models import TaoDividend, StakeTransaction, SentimentAnalysis
import os


@pytest.mark.asyncio
async def test_tao_dividends_endpoint_unauthorized(client):
    """Test that the endpoint requires authentication."""
    response = client.get("/api/v1/tao_dividends")
    assert response.status_code == 403
    assert "Invalid API Key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_tao_dividends_endpoint_success(client, db_session):
    """Test successful Tao dividends retrieval."""
    api_key = os.getenv("API_KEY", "test_key")
    
    # Mock Redis and blockchain responses
    with patch("app.services.redis_client") as mock_redis, \
         patch("app.services.subtensor") as mock_subtensor:
        
        mock_redis.get.return_value = None
        mock_subtensor.tao_dividends_per_hotkey.return_value = 100.0
        
        response = client.get(
            "/api/v1/tao_dividends?netuid=18&hotkey=test_hotkey",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == 100.0
        assert data["cached"] is False


@pytest.mark.asyncio
async def test_tao_dividends_endpoint_cached(client, db_session):
    """Test Tao dividends retrieval from cache."""
    api_key = os.getenv("API_KEY", "test_key")
    
    # Mock Redis response
    with patch("app.services.redis_client") as mock_redis:
        mock_redis.get.return_value = "150.0"
        
        response = client.get(
            "/api/v1/tao_dividends?netuid=18&hotkey=test_hotkey",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == "150.0"
        assert data["cached"] is True


@pytest.mark.asyncio
async def test_tao_dividends_with_trade(client, db_session):
    """Test Tao dividends retrieval with trade option."""
    api_key = os.getenv("API_KEY", "test_key")
    
    # Mock all external services
    with patch("app.services.redis_client") as mock_redis, \
         patch("app.services.subtensor") as mock_subtensor, \
         patch("app.services.trigger_stake") as mock_trigger_stake:
        
        mock_redis.get.return_value = None
        mock_subtensor.tao_dividends_per_hotkey.return_value = 100.0
        
        response = client.get(
            "/api/v1/tao_dividends?netuid=18&hotkey=test_hotkey&trade=true",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["stake_triggered"] is True
        mock_trigger_stake.apply_async.assert_called_once()


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy" 