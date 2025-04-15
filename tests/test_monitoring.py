import pytest
from unittest.mock import patch
from app.models import TaoDividend, StakeTransaction, SentimentAnalysis
from sqlalchemy import insert
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_stats_endpoint(client, db_session):
    """Test the stats monitoring endpoint."""
    # Insert test data
    await db_session.execute(
        insert(TaoDividend).values([
            {
                "netuid": 18,
                "hotkey": "test_hotkey",
                "dividend_amount": 100.0,
                "timestamp": datetime.utcnow()
            }
        ])
    )
    await db_session.execute(
        insert(StakeTransaction).values([
            {
                "netuid": 18,
                "hotkey": "test_hotkey",
                "amount": 50.0,
                "transaction_type": "stake",
                "sentiment_score": 75.0,
                "status": "completed",
                "timestamp": datetime.utcnow()
            }
        ])
    )
    await db_session.commit()
    
    # Mock Redis info
    with patch("app.monitoring.redis_client.info") as mock_info:
        mock_info.return_value = {
            "connected_clients": 1,
            "used_memory_human": "1.00M",
            "total_connections_received": 100
        }
        
        response = client.get("/monitoring/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert data["database"]["dividend_records"] == 1
        assert data["database"]["transaction_records"] == 1
        assert data["redis"]["connected_clients"] == 1


@pytest.mark.asyncio
async def test_recent_transactions_endpoint(client, db_session):
    """Test the recent transactions monitoring endpoint."""
    # Insert test transactions
    now = datetime.utcnow()
    transactions = [
        {
            "netuid": 18,
            "hotkey": f"test_hotkey_{i}",
            "amount": float(i * 10),
            "transaction_type": "stake" if i % 2 == 0 else "unstake",
            "sentiment_score": float(i * 5),
            "status": "completed",
            "timestamp": now - timedelta(minutes=i)
        }
        for i in range(5)
    ]
    
    await db_session.execute(insert(StakeTransaction).values(transactions))
    await db_session.commit()
    
    response = client.get("/monitoring/recent_transactions?limit=3")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 3
    assert data[0]["hotkey"] == "test_hotkey_0"
    assert data[1]["hotkey"] == "test_hotkey_1"
    assert data[2]["hotkey"] == "test_hotkey_2"


@pytest.mark.asyncio
async def test_sentiment_analysis_endpoint(client, db_session):
    """Test the sentiment analysis monitoring endpoint."""
    # Insert test sentiment analyses
    analyses = [
        {
            "netuid": 18,
            "sentiment_score": 75.0,
            "tweet_count": 10,
            "timestamp": datetime.utcnow(),
            "source": "datura"
        },
        {
            "netuid": 18,
            "sentiment_score": 25.0,
            "tweet_count": 5,
            "timestamp": datetime.utcnow(),
            "source": "datura"
        }
    ]
    
    await db_session.execute(insert(SentimentAnalysis).values(analyses))
    await db_session.commit()
    
    response = client.get("/monitoring/sentiment_analysis")
    assert response.status_code == 200
    data = response.json()
    
    assert "18" in data
    assert data["18"]["average_sentiment"] == 50.0  # (75 + 25) / 2
    assert data["18"]["total_analyses"] == 2 