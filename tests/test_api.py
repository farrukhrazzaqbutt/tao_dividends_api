import pytest
from unittest.mock import patch, MagicMock
import os
import json


@pytest.mark.asyncio
async def test_tao_dividends_endpoint_unauthorized(client):
    """Test unauthorized access to tao dividends endpoint."""
    response = client.get("/api/v1/tao_dividends?netuid=18&hotkey=test_hotkey")
    assert response.status_code == 401
    data = response.json()
    assert "Not authenticated" in str(data["detail"])


@pytest.mark.asyncio
async def test_tao_dividends_endpoint_success(client):
    """Test successful access to tao dividends endpoint."""
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
            "/api/v1/tao_dividends?netuid=18&hotkey=test_hotkey",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "dividends" in data
        assert "hotkey" in data
        assert "netuid" in data
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_tao_dividends_endpoint_cached(client):
    """Test cached response from tao dividends endpoint."""
    api_key = os.getenv("API_TOKEN", "test_key")
    
    # Mock Redis to return a cached value
    with patch("app.services.redis_client") as mock_redis:
        cached_data = {
            "dividends": 100.0, 
            "hotkey": "test_hotkey", 
            "netuid": 18, 
            "timestamp": "2024-01-01T00:00:00"
        }
        mock_redis.get.return_value = json.dumps(cached_data)
        
        response = client.get(
            "/api/v1/tao_dividends?netuid=18&hotkey=test_hotkey",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "dividends" in data
        assert "hotkey" in data
        assert "netuid" in data
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_tao_dividends_with_trade(client):
    """Test tao dividends endpoint with trade flag."""
    api_key = os.getenv("API_TOKEN", "test_key")
    test_hotkey = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
    
    # Mock all external services
    with patch("app.services.redis_client") as mock_redis, \
         patch("app.utils.Subtensor") as mock_subtensor, \
         patch("app.utils.get_sentiment") as mock_get_sentiment, \
         patch("app.worker.trigger_stake_task") as mock_trigger_stake:
        
        mock_redis.get.return_value = None
        mock_instance = MagicMock()
        mock_subtensor.return_value = mock_instance
        mock_instance.get_tao_dividends.return_value = {test_hotkey: 100.0}
        mock_get_sentiment.return_value = 80.0
        mock_trigger_stake.delay.return_value = MagicMock(id="mock_task_id")
        
        response = client.get(
            f"/api/v1/tao_dividends?netuid=18&hotkey={test_hotkey}&trade=true",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"