from celery import Celery
import os
from dotenv import load_dotenv
import logging
from app.utils import Subtensor
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "tao_dividends",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

# Initialize Subtensor
subtensor = Subtensor()

@celery_app.task(name="trigger_stake")
def trigger_stake_task(netuid: int, hotkey: str, sentiment_score: float):
    """
    Celery task to perform stake operation based on sentiment score.
    
    Args:
        netuid: The subnet ID
        hotkey: The hotkey address
        sentiment_score: Sentiment score between -100 and +100
        
    Returns:
        Dict containing operation status and details
    """
    try:
        logger.info(f"Starting stake operation for netuid {netuid}, hotkey {hotkey}")
        
        # Calculate stake amount based on sentiment
        if sentiment_score > 50:
            stake_amount = 100  # High positive sentiment
        elif sentiment_score > 0:
            stake_amount = 50   # Moderate positive sentiment
        elif sentiment_score > -50:
            stake_amount = 25   # Moderate negative sentiment
        else:
            stake_amount = 0    # Very negative sentiment
            
        # Perform stake operation
        success = subtensor.add_stake(netuid, hotkey, stake_amount)
        
        # Prepare response
        response = {
            "netuid": netuid,
            "hotkey": hotkey,
            "sentiment_score": sentiment_score,
            "stake_amount": stake_amount,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if success:
            logger.info(f"Stake operation completed successfully: {response}")
        else:
            logger.error(f"Stake operation failed: {response}")
            
        return response
        
    except Exception as e:
        logger.error(f"Error in stake operation: {str(e)}")
        return {
            "netuid": netuid,
            "hotkey": hotkey,
            "sentiment_score": sentiment_score,
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }



def without_celery_trigger_stake_task(netuid: int, hotkey: str, sentiment_score: float):
    """
    Celery task to perform stake operation based on sentiment score.
    
    Args:
        netuid: The subnet ID
        hotkey: The hotkey address
        sentiment_score: Sentiment score between -100 and +100
        
    Returns:
        Dict containing operation status and details
    """
    try:
        logger.info(f"Starting stake operation for netuid {netuid}, hotkey {hotkey}")
        
        # Calculate stake amount based on sentiment
        if sentiment_score > 50:
            stake_amount = 100  # High positive sentiment
        elif sentiment_score > 0:
            stake_amount = 50   # Moderate positive sentiment
        elif sentiment_score > -50:
            stake_amount = 25   # Moderate negative sentiment
        else:
            stake_amount = 0    # Very negative sentiment
            
        # Perform stake operation
        success = subtensor.add_stake(netuid, hotkey, stake_amount)
        
        # Prepare response
        response = {
            "netuid": netuid,
            "hotkey": hotkey,
            "sentiment_score": sentiment_score,
            "stake_amount": stake_amount,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if success:
            logger.info(f"Stake operation completed successfully: {response}")
        else:
            logger.error(f"Stake operation failed: {response}")
            
        return response
        
    except Exception as e:
        logger.error(f"Error in stake operation: {str(e)}")
        return {
            "netuid": netuid,
            "hotkey": hotkey,
            "sentiment_score": sentiment_score,
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
