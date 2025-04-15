# Tao Dividends API

A production-grade asynchronous API service for querying Tao dividends from the Bittensor blockchain and managing stakes based on Twitter sentiment analysis.

## Features

- Asynchronous FastAPI endpoint for querying Tao dividends
- Redis caching for blockchain query results
- Twitter sentiment analysis using Datura.ai and Chutes.ai
- Automated stake/unstake operations based on sentiment
- Celery workers for background tasks
- PostgreSQL database for historical data
- Docker containerization
- API key authentication
- Comprehensive error handling and logging

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- PostgreSQL 13+
- Redis 6+

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd tao-dividends-api
```

2. Create and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Build and start the services:
```bash
docker-compose up --build
```

The API will be available at http://localhost:8000

## API Documentation

Once the service is running, visit http://localhost:8000/docs for interactive API documentation.

### Main Endpoint

`GET /api/v1/tao_dividends`

Query parameters:
- `netuid` (int, optional): Subnet ID (default: 18)
- `hotkey` (str, optional): Account ID (default: "")
- `trade` (bool, optional): Whether to trigger sentiment-based staking (default: false)

Headers:
- `X-API-Key`: Your API key for authentication

Example request:
```bash
curl -X GET "http://localhost:8000/api/v1/tao_dividends?netuid=18&hotkey=5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v" \
     -H "X-API-Key: your_api_key_here"
```

## Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest
```

3. Start services individually:
```bash
# Start PostgreSQL
docker-compose up db

# Start Redis
docker-compose up redis

# Start API
uvicorn app.main:app --reload

# Start Celery worker
celery -A app.worker worker --loglevel=info
```

## Architecture

The service follows a modern async architecture:

- FastAPI handles HTTP requests
- Redis serves as cache and message broker
- Celery workers process background tasks
- PostgreSQL stores historical data
- Docker containers orchestrate all components

## Error Handling

The API implements comprehensive error handling:

- 400 Bad Request: Invalid parameters
- 401 Unauthorized: Missing or invalid API key
- 403 Forbidden: Invalid permissions
- 500 Internal Server Error: Server-side errors

All errors are logged with appropriate context.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
