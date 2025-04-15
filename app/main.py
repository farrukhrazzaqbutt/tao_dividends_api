from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db, init_db
from app.models import Subnet, Dividend, Operation
from app.services import get_tao_dividends, trigger_stake
from app.monitoring import router as monitoring_router
from app.worker import trigger_stake_task, without_celery_trigger_stake_task
from app.cache import get_cached_dividends, cache_dividends
from typing import List, Dict, Optional
import logging
import asyncio
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import redis
import json
from app.utils import Subtensor, get_sentiment, perform_stake
from fastapi import status

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Tao Dividends API",
    description="API for querying Tao dividends and performing stake operations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# OAuth2 scheme for API authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Default parameters
DEFAULT_NETUID = 18
DEFAULT_HOTKEY = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"

async def verify_token(token: str = Depends(oauth2_scheme)):
    """Verify the API token."""
    logger.info(f"Received token: {token}")
    logger.info(f"Expected token: {os.getenv('API_TOKEN')}")
    if token != os.getenv("API_TOKEN"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

def get_cached_dividends(netuid: int, hotkey: str = "") -> Optional[Dict]:
    """Get cached dividends from Redis."""
    cache_key = f"dividends:{netuid}:{hotkey}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None

def cache_dividends(netuid: int, hotkey: str, data: Dict):
    """Cache dividends in Redis for 2 minutes."""
    cache_key = f"dividends:{netuid}:{hotkey}"
    # redis_client.setex(
    #     cache_key,
    #     timedelta(minutes=2),
    #     json.dumps(data)
    # )

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()

@app.get("/api/v1/tao_dividends")
async def tao_dividends(
    netuid: Optional[int] = Query(DEFAULT_NETUID, description="Subnet ID"),
    hotkey: Optional[str] = Query(DEFAULT_HOTKEY, description="Hotkey address"),
    trade: bool = Query(False, description="Whether to perform stake operation"),
    token: str = Depends(verify_token)
):
    """
    Get Tao dividends for a subnet and optionally perform stake operation.
    
    Args:
        netuid: The subnet ID (default: 18)
        hotkey: The hotkey address
        trade: Whether to perform stake operation based on sentiment
        token: API authentication token
        
    Returns:
        Dict containing dividends data and stake operation status
    """
    try:
        logger.info(f"Fetching Tao dividends for netuid {netuid}, hotkey {hotkey}")
        
        # Check cache first
        cached_data = get_cached_dividends(netuid, hotkey)
        if cached_data:
            logger.info("Returning cached dividends data")
            return cached_data
            
        # Create Subtensor instance
        subtensor = Subtensor()
        
        # Get dividends from blockchain - note this is not async
        dividends = subtensor.get_tao_dividends(netuid, hotkey)
        
        # Prepare response
        response = {
            "netuid": netuid,
            "hotkey": hotkey,
            "dividends": dividends,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache the response
        cache_dividends(netuid, hotkey, response)
        
        # If trade is True, trigger stake operation
        if trade:
            logger.info("Trade flag is True, triggering stake operation")
            
            # Get sentiment score
            sentiment_score = await get_sentiment(netuid, hotkey)
            logger.info(f"Sentiment score: {sentiment_score}")
            
            # Convert sentiment_score to float if it's a string
            if isinstance(sentiment_score, str):
                sentiment_score = float(sentiment_score)
            
            # Ensure hotkey is not empty
            if not hotkey or hotkey.strip() == "":
                logger.error("Empty hotkey address provided")
                response["trade"] = {
                    "triggered": True,
                    "error": "Empty hotkey address provided",
                    "sentiment_score": sentiment_score,
                    "success": False
                }
                return response
            
            # Trigger stake operation as Celery task
            task_result = trigger_stake_task.delay(netuid, hotkey, sentiment_score)
            
            # Add task info to response
            response["trade"] = {
                "triggered": True,
                "task_id": task_result.id,  # Celery task has an id attribute
                "sentiment_score": sentiment_score,
                "success": True  # We assume success since the task was queued
            }
        else:
            response["trade"] = {"triggered": False}
            
        return response
        
    except Exception as e:
        logger.error(f"Error in tao_dividends endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/v1/operations")
async def get_operations(
    netuid: Optional[int] = Query(None, description="Filter by subnet ID"),
    hotkey: Optional[str] = Query(None, description="Filter by hotkey address"),
    token: str = Depends(verify_token)
):
    """
    Get historical stake operations.
    
    Args:
        netuid: Filter operations by subnet ID
        hotkey: Filter operations by hotkey address
        token: API authentication token
        
    Returns:
        List of historical operations
    """
    try:
        # Get operations from database
        operations = []  # TODO: Implement database query
        
        # Apply filters
        if netuid:
            operations = [op for op in operations if op["netuid"] == netuid]
        if hotkey:
            operations = [op for op in operations if op["hotkey"] == hotkey]
            
        return {
            "operations": operations,
            "count": len(operations)
        }
        
    except Exception as e:
        logger.error(f"Error in get_operations endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
