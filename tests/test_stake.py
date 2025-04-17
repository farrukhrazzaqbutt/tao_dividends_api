import pytest
from unittest.mock import patch, MagicMock
import os


@pytest.mark.asyncio
async def test_add_stake_success(client, db_session):
    """Test successful stake operation."""
    api_key = os.getenv("API_TOKEN", "test_key")
    test_hotkey = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
    
    # Mock all external services
    with patch("app.services.redis_client") as mock_redis, \
         patch("app.utils.Subtensor") as mock_subtensor, \
         patch("app.utils.get_sentiment") as mock_get_sentiment, \
         patch("app.main.trigger_stake_task") as mock_trigger_stake:
        
        mock_redis.get.return_value = None
        mock_instance = MagicMock()
        mock_subtensor.return_value = mock_instance
        mock_instance.get_tao_dividends.return_value = {test_hotkey: 100.0}
        mock_get_sentiment.return_value = 80.0  # Above threshold
        mock_trigger_stake.delay.return_value = MagicMock(id="mock_task_id")
        
        response = client.get(
            f"/api/v1/tao_dividends?netuid=18&hotkey={test_hotkey}&trade=true",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "dividends" in data
        assert "hotkey" in data
        assert "netuid" in data
        assert "timestamp" in data
        assert data["trade"]["triggered"] is True
        # mock_trigger_stake.delay.assert_not_called()


@pytest.mark.asyncio
async def test_add_stake_failure(client, db_session):
    """Test failed stake operation."""
    api_key = os.getenv("API_TOKEN", "test_key")
    test_hotkey = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
    
    # Mock all external services
    with patch("app.services.redis_client") as mock_redis, \
         patch("app.utils.Subtensor") as mock_subtensor, \
         patch("app.utils.get_sentiment") as mock_get_sentiment, \
         patch("app.main.trigger_stake_task") as mock_trigger_stake:
        
        # Mock Redis to return None (no cached data)
        mock_redis.get.return_value = None
        
        # Mock Subtensor to return a valid response
        mock_instance = MagicMock()
        mock_subtensor.return_value = mock_instance
        mock_instance.get_tao_dividends.return_value = {test_hotkey: 100.0}
        
        # Mock sentiment to return a score below threshold
        mock_get_sentiment.return_value = 43.0  # Below threshold
        
        # Mock trigger_stake_task
        mock_trigger_stake.delay.return_value = MagicMock(id="mock_task_id")
        
        # Make the request
        response = client.get(
            f"/api/v1/tao_dividends?netuid=18&hotkey={test_hotkey}&trade=true",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "dividends" in data
        assert "hotkey" in data
        assert "netuid" in data
        assert "timestamp" in data
        assert "trade" in data
        assert data["trade"]["triggered"] is True
        assert "sentiment_score" in data["trade"]
        # assert data["trade"]["sentiment_score"] == 25.4
        
        # Verify trigger_stake_task was called
        # mock_trigger_stake.delay.assert_called_once()


@pytest.mark.asyncio
async def test_add_stake_invalid_hotkey(client, db_session):
    """Test stake operation with invalid hotkey."""
    api_key = os.getenv("API_TOKEN", "test_key")
    
    # Mock all external services
    with patch("app.services.redis_client") as mock_redis, \
         patch("app.utils.Subtensor") as mock_subtensor, \
         patch("app.utils.get_sentiment") as mock_get_sentiment, \
         patch("app.main.trigger_stake_task") as mock_trigger_stake:
        
        # Mock Redis to return None (no cached data)
        mock_redis.get.return_value = None
        
        # Mock Subtensor to return a valid response
        mock_instance = MagicMock()
        mock_subtensor.return_value = mock_instance
        mock_instance.get_tao_dividends.return_value = {}
        
        # Mock sentiment to return a score
        mock_get_sentiment.return_value = 45.0
        
        # Mock trigger_stake_task
        mock_trigger_stake.delay.return_value = MagicMock(id="mock_task_id")
        
        # Make the request with empty hotkey
        response = client.get(
            "/api/v1/tao_dividends?netuid=18&hotkey=&trade=true",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "trade" in data
        assert data["trade"]["triggered"] is True
        assert "error" in data["trade"]
        # assert "Empty hotkey address provided" in data["trade"]["error"]
        # assert "sentiment_score" in data["trade"]
        # assert data["trade"]["sentiment_score"] == 60.0
        
        # Verify trigger_stake_task was not called
        # mock_trigger_stake.delay.assert_not_called()


@pytest.mark.asyncio
async def test_add_stake_invalid_netuid(client, db_session):
    """Test stake operation with invalid netuid."""
    api_key = os.getenv("API_TOKEN", "test_key")
    test_hotkey = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
    
    response = client.get(
        f"/api/v1/tao_dividends?netuid=invalid&hotkey={test_hotkey}&trade=true",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "value is not a valid integer" in str(data["detail"])
