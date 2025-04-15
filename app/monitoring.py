from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Subnet, Dividend, Operation, SentimentAnalysis
from typing import Dict, List
import redis
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)) -> Dict:
    """Get system statistics."""
    try:
        # Database stats
        dividend_count = await db.scalar(
            select(func.count()).select_from(Dividend)
        )
        transaction_count = await db.scalar(
            select(func.count()).select_from(Operation)
        )
        sentiment_count = await db.scalar(
            select(func.count()).select_from(SentimentAnalysis)
        )
        
        # Redis stats
        redis_info = redis_client.info()
        
        return {
            "database": {
                "dividend_records": dividend_count,
                "transaction_records": transaction_count,
                "sentiment_records": sentiment_count
            },
            "redis": {
                "connected_clients": redis_info["connected_clients"],
                "used_memory_human": redis_info["used_memory_human"],
                "total_connections_received": redis_info["total_connections_received"]
            }
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/recent_transactions")
async def get_recent_transactions(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
) -> List[Dict]:
    """Get most recent stake transactions."""
    try:
        query = select(Operation).order_by(
            Operation.timestamp.desc()
        ).limit(limit)
        
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        return [
            {
                "id": tx.id,
                "netuid": tx.netuid,
                "hotkey": tx.hotkey,
                "amount": tx.amount,
                "type": tx.operation_type,
                "status": tx.status,
                "timestamp": tx.timestamp.isoformat()
            }
            for tx in transactions
        ]
    except Exception as e:
        return {"error": str(e)}

@router.get("/sentiment_analysis")
async def get_sentiment_stats(db: AsyncSession = Depends(get_db)) -> Dict:
    """Get sentiment analysis statistics."""
    try:
        query = select(
            SentimentAnalysis.netuid,
            func.avg(SentimentAnalysis.sentiment_score).label("avg_score"),
            func.count().label("count")
        ).group_by(SentimentAnalysis.netuid)
        
        result = await db.execute(query)
        stats = result.all()
        
        return {
            str(stat.netuid): {
                "average_sentiment": float(stat.avg_score),
                "total_analyses": stat.count
            }
            for stat in stats
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/dividends", response_model=List[Dict])
async def get_dividends(
    netuid: int = None,
    hotkey: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get dividend history."""
    try:
        query = select(Dividend)
        
        if netuid:
            subnet = await db.execute(
                select(Subnet).where(Subnet.netuid == netuid)
            )
            subnet = subnet.scalar_one_or_none()
            if subnet:
                query = query.where(Dividend.subnet_id == subnet.id)
                
        if hotkey:
            query = query.where(Dividend.hotkey == hotkey)
            
        result = await db.execute(query)
        dividends = result.scalars().all()
        
        return [
            {
                "netuid": (await db.execute(
                    select(Subnet).where(Subnet.id == div.subnet_id)
                )).scalar_one().netuid,
                "hotkey": div.hotkey,
                "amount": div.amount,
                "timestamp": div.timestamp.isoformat()
            }
            for div in dividends
        ]
        
    except Exception as e:
        logger.error(f"Error getting dividends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/operations", response_model=List[Dict])
async def get_operations(
    netuid: int = None,
    hotkey: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get operation history."""
    try:
        query = select(Operation)
        
        if netuid:
            subnet = await db.execute(
                select(Subnet).where(Subnet.netuid == netuid)
            )
            subnet = subnet.scalar_one_or_none()
            if subnet:
                query = query.where(Operation.subnet_id == subnet.id)
                
        if hotkey:
            query = query.where(Operation.hotkey == hotkey)
            
        result = await db.execute(query)
        operations = result.scalars().all()
        
        return [
            {
                "netuid": (await db.execute(
                    select(Subnet).where(Subnet.id == op.subnet_id)
                )).scalar_one().netuid,
                "hotkey": op.hotkey,
                "amount": op.amount,
                "sentiment_score": op.sentiment_score,
                "operation_type": op.operation_type,
                "status": op.status,
                "timestamp": op.timestamp.isoformat()
            }
            for op in operations
        ]
        
    except Exception as e:
        logger.error(f"Error getting operations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 