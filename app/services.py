import httpx
import redis
# from bittensor import AsyncSubtensor, wallet
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Subnet, Dividend, Operation
from app.utils import get_sentiment, perform_stake, Subtensor
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

logger = logging.getLogger(__name__)

# Try to connect to Redis, fallback to None if not available
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0,
        decode_responses=True
    )
    # Test the connection
    redis_client.ping()
    logger.info("Successfully connected to Redis")
except (redis.ConnectionError, redis.ResponseError) as e:
    logger.warning(f"Could not connect to Redis: {str(e)}. Running without cache.")
    redis_client = None

# Initialize Subtensor
subtensor = Subtensor()

async def get_tao_dividends(netuid: int, hotkey: str = "") -> Dict[str, float]:
    """
    Get Tao dividends for a subnet and hotkey.
    
    Args:
        netuid: The subnet ID
        hotkey: The hotkey address
        
    Returns:
        Dict[str, float]: Dictionary of hotkey to dividend amount
    """
    try:
        logger.info(f"Getting Tao dividends for netuid {netuid}, hotkey {hotkey}")
        
        # Query the chain for TaoDividendsPerSubnet
        result = subtensor.get_tao_dividends(netuid, hotkey)
        
        if not result:
            logger.warning(f"No dividends found for netuid {netuid}")
            return {}
            
        # Process the result
        dividends = {}
        for key, value in result.items():
            if hotkey and key != hotkey:
                continue
            dividends[key] = float(value)
            
        return dividends
        
    except Exception as e:
        logger.error(f"Error getting Tao dividends: {str(e)}")
        return {}

async def trigger_stake(
    netuid: int,
    hotkey: str,
    db: AsyncSession = None
) -> Dict:
    """Trigger stake operation."""
    try:
        if not db:
            from app.database import get_db
            db = await anext(get_db())
            
        # Get sentiment score
        sentiment_score = await get_sentiment(netuid, hotkey)
        
        if not sentiment_score or sentiment_score <= 70:
            return {
                "status": "skipped",
                "reason": "sentiment_score_too_low",
                "sentiment_score": sentiment_score
            }
            
        # Perform stake operation
        result = await perform_stake(netuid, hotkey)
        
        # Record operation
        operation = Operation(
            subnet_id=netuid,
            hotkey=hotkey,
            amount=result.get("amount", 0),
            sentiment_score=sentiment_score,
            operation_type="stake",
            status="completed"
        )
        db.add(operation)
        await db.commit()
        
        return {
            "status": "success",
            "operation": "stake",
            "sentiment_score": sentiment_score,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error in trigger_stake: {str(e)}")
        raise
