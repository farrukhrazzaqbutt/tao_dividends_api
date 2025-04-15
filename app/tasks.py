from celery import Celery
from app.utils import get_sentiment, perform_stake, perform_unstake
from app.models import Operation, Subnet, Dividend
from sqlalchemy.orm import Session
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "tao_dividends",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
async def analyze_sentiment_and_stake(netuid: int, hotkey: str) -> Dict:
    """Analyze sentiment and perform stake/unstake operation."""
    try:
        # Get sentiment score
        sentiment_score = await get_sentiment(netuid)
        
        # Calculate stake amount based on sentiment (-100 to +100)
        # Scale to 0-1 and multiply by max stake amount
        max_stake = 100.0  # Maximum stake amount in TAO
        stake_amount = (sentiment_score + 100) / 200 * max_stake
        
        # Perform stake or unstake based on sentiment
        if sentiment_score > 0:
            success = await perform_stake(netuid, hotkey, stake_amount)
            operation_type = "stake"
        else:
            success = await perform_unstake(netuid, hotkey, abs(stake_amount))
            operation_type = "unstake"
            
        return {
            "success": success,
            "sentiment_score": sentiment_score,
            "amount": stake_amount,
            "operation_type": operation_type
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_sentiment_and_stake: {str(e)}")
        raise

@celery_app.task
async def cache_dividends(netuid: int, dividends: List[Dict]) -> bool:
    """Cache dividend data in Redis."""
    try:
        from app.cache import cache
        cache_key = f"dividends:netuid:{netuid}"
        return await cache.set(cache_key, dividends)
    except Exception as e:
        logger.error(f"Error caching dividends: {str(e)}")
        return False

@celery_app.task
async def store_operation(
    netuid: int,
    hotkey: str,
    amount: float,
    sentiment_score: float,
    operation_type: str,
    status: str
) -> bool:
    """Store operation in database."""
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        
        # Get or create subnet
        subnet = db.query(Subnet).filter(Subnet.netuid == netuid).first()
        if not subnet:
            subnet = Subnet(netuid=netuid)
            db.add(subnet)
            db.commit()
            
        # Create operation record
        operation = Operation(
            subnet_id=subnet.id,
            hotkey=hotkey,
            amount=amount,
            sentiment_score=sentiment_score,
            operation_type=operation_type,
            status=status
        )
        
        db.add(operation)
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error storing operation: {str(e)}")
        return False
    finally:
        db.close() 