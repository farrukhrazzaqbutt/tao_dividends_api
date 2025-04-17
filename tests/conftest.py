import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models import Base
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///./test.db"
)

# Create test engine
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
    future=True
)

# Create test session
TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Create test database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        yield engine
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception as e:
        logger.error(f"Error setting up test database: {e}")
        raise

@pytest.fixture
async def db_session(test_db):
    """Create a fresh database session for a test."""
    async_session = TestingSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.close()

@pytest.fixture
def client(db_session):
    """Create a test client with a database session."""
    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Set default API key for testing
    os.environ["API_TOKEN"] = "test_key"
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
    # Clean up environment variable
    if "API_TOKEN" in os.environ:
        del os.environ["API_TOKEN"] 