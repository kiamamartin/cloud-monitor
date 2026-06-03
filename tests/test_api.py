import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio

async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        
        # Accept 200 (Local Dev) or 503 (CI Pipeline without DB)
        assert response.status_code in [200, 503]
        
        data = response.json()
        if response.status_code == 503:
            assert "detail" in data
            assert data["detail"]["api"] == "healthy"
        else:
            assert "api" in data
            assert data["api"] == "healthy"
