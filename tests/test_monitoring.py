import pytest
import os
from datetime import datetime
from app.models import Operation


@pytest.mark.asyncio
async def test_operations_endpoint_unauthorized(client):
    """Test unauthorized access to operations endpoint."""
    response = client.get("/api/v1/operations")
    assert response.status_code == 401
    data = response.json()
    assert "Not authenticated" in str(data["detail"])