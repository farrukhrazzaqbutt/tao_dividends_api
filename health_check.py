import requests
import redis
import psycopg2
import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_fastapi():
    """Check if FastAPI is running"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ FastAPI is running")
            return True
        else:
            print("❌ FastAPI returned status code:", response.status_code)
            return False
    except Exception as e:
        print("❌ FastAPI check failed:", str(e))
        return False

def check_redis():
    """Check if Redis is running"""
    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True
        )
        redis_client.ping()
        print("✅ Redis is running")
        return True
    except Exception as e:
        print("❌ Redis check failed:", str(e))
        return False

def check_postgres():
    """Check if PostgreSQL is running"""
    try:
        conn = psycopg2.connect(
            os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/tao_dividends")
        )
        conn.close()
        print("✅ PostgreSQL is running")
        return True
    except Exception as e:
        print("❌ PostgreSQL check failed:", str(e))
        return False

def check_celery():
    """Check if Celery worker is running"""
    try:
        from celery import Celery
        app = Celery('tao_dividends')
        app.conf.broker_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        app.conf.result_backend = os.getenv("REDIS_URL", "redis://redis:6379/0")
        
        # Try to ping the worker
        app.control.ping(timeout=1.0)
        print("✅ Celery worker is running")
        return True
    except Exception as e:
        print("❌ Celery check failed:", str(e))
        return False

def main():
    """Run all health checks"""
    print("Running health checks...")
    
    # Check FastAPI
    fastapi_ok = check_fastapi()
    
    # Check Redis
    redis_ok = check_redis()
    
    # Check PostgreSQL
    postgres_ok = check_postgres()
    
    # Check Celery
    celery_ok = check_celery()
    
    # Summary
    print("\nHealth Check Summary:")
    print("====================")
    print(f"FastAPI:   {'✅' if fastapi_ok else '❌'}")
    print(f"Redis:     {'✅' if redis_ok else '❌'}")
    print(f"PostgreSQL: {'✅' if postgres_ok else '❌'}")
    print(f"Celery:    {'✅' if celery_ok else '❌'}")
    
    # Exit with appropriate code
    if all([fastapi_ok, redis_ok, postgres_ok, celery_ok]):
        print("\n✅ All services are running correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some services are not running correctly.")
        sys.exit(1)

if __name__ == "__main__":
    main() 