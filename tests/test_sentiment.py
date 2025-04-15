import pytest
from unittest.mock import patch, MagicMock
from app.utils import get_sentiment, analyze_sentiment, perform_stake, perform_unstake
import httpx
from datetime import datetime

@pytest.mark.asyncio
async def test_get_sentiment():
    """Test sentiment analysis from Twitter data."""
    # Mock Datura API response
    mock_tweets = {
        "tweets": [
            {"text": "Bittensor netuid 18 is amazing!", "created_at": datetime.utcnow().isoformat()},
            {"text": "Great project with Bittensor netuid 18", "created_at": datetime.utcnow().isoformat()}
        ]
    }
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_tweets
        )
        
        # Mock Chutes API response
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"sentiment_score": 75.0}
            )
            
            sentiment_score = await get_sentiment(18)
            assert sentiment_score == 75.0

@pytest.mark.asyncio
async def test_analyze_sentiment():
    """Test sentiment analysis using Chutes.ai."""
    tweets = [
        {"text": "Positive tweet about Bittensor", "created_at": datetime.utcnow().isoformat()},
        {"text": "Another positive tweet", "created_at": datetime.utcnow().isoformat()}
    ]
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"sentiment_score": 80.0}
        )
        
        sentiment_score = await analyze_sentiment(tweets)
        assert sentiment_score == 80.0

@pytest.mark.asyncio
async def test_perform_stake():
    """Test stake operation."""
    with patch("app.utils.subtensor") as mock_subtensor:
        mock_subtensor.add_stake.return_value = True
        
        result = await perform_stake(18, "test_hotkey", 1.0)
        assert result is True
        mock_subtensor.add_stake.assert_called_once()

@pytest.mark.asyncio
async def test_perform_unstake():
    """Test unstake operation."""
    with patch("app.utils.subtensor") as mock_subtensor:
        mock_subtensor.unstake.return_value = True
        
        result = await perform_unstake(18, "test_hotkey", 1.0)
        assert result is True
        mock_subtensor.unstake.assert_called_once()

@pytest.mark.asyncio
async def test_sentiment_based_staking():
    """Test the complete sentiment-based staking flow."""
    # Mock Datura API response
    mock_tweets = {
        "tweets": [
            {"text": "Bittensor netuid 18 is performing well", "created_at": datetime.utcnow().isoformat()},
            {"text": "Great progress with subnet 18", "created_at": datetime.utcnow().isoformat()}
        ]
    }
    
    with patch("httpx.AsyncClient.get") as mock_get, \
         patch("httpx.AsyncClient.post") as mock_post, \
         patch("app.utils.subtensor") as mock_subtensor:
        
        # Mock Datura API
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_tweets
        )
        
        # Mock Chutes API
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"sentiment_score": 75.0}
        )
        
        # Mock Bittensor operations
        mock_subtensor.add_stake.return_value = True
        
        # Test positive sentiment (should stake)
        sentiment_score = await get_sentiment(18)
        assert sentiment_score == 75.0
        
        # Calculate stake amount
        stake_amount = 0.01 * sentiment_score
        assert stake_amount == 0.75
        
        # Perform stake
        result = await perform_stake(18, "test_hotkey", stake_amount)
        assert result is True

@pytest.mark.asyncio
async def test_sentiment_based_unstaking():
    """Test the complete sentiment-based unstaking flow."""
    # Mock Datura API response with negative sentiment
    mock_tweets = {
        "tweets": [
            {"text": "Bittensor netuid 18 is having issues", "created_at": datetime.utcnow().isoformat()},
            {"text": "Problems with subnet 18", "created_at": datetime.utcnow().isoformat()}
        ]
    }
    
    with patch("httpx.AsyncClient.get") as mock_get, \
         patch("httpx.AsyncClient.post") as mock_post, \
         patch("app.utils.subtensor") as mock_subtensor:
        
        # Mock Datura API
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_tweets
        )
        
        # Mock Chutes API with negative sentiment
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"sentiment_score": -50.0}
        )
        
        # Mock Bittensor operations
        mock_subtensor.unstake.return_value = True
        
        # Test negative sentiment (should unstake)
        sentiment_score = await get_sentiment(18)
        assert sentiment_score == -50.0
        
        # Calculate unstake amount
        unstake_amount = 0.01 * abs(sentiment_score)
        assert unstake_amount == 0.5
        
        # Perform unstake
        result = await perform_unstake(18, "test_hotkey", unstake_amount)
        assert result is True 