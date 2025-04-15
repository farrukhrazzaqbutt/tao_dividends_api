# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker
# import os
# from dotenv import load_dotenv

# load_dotenv()

# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "postgresql+asyncpg://postgres:postgres@localhost:5432/tao_dividends"
# )

# engine = create_async_engine(
#     DATABASE_URL,
#     echo=True,
#     future=True
# )

# AsyncSessionLocal = sessionmaker(
#     engine,
#     class_=AsyncSession,
#     expire_on_commit=False
# )

# async def get_db():
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#         finally:
#             await session.close() 

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Initialize the database by creating all tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


async def get_db():
    async with SessionLocal() as session:
        yield session