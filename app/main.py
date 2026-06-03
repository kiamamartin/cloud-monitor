from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.database import get_db
from app.api.endpoints import monitors

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Start Prometheus Instrumentator
Instrumentator().instrument(app).expose(app)

redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)

async def get_redis():
    return redis.Redis(connection_pool=redis_pool)

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    cache: redis.Redis = Depends(get_redis)
):
    status = {"api": "healthy", "database": "unknown", "redis": "unknown"}
    
    try:
        await db.execute(text("SELECT 1"))
        status["database"] = "healthy"
    except Exception as e:
        status["database"] = f"unhealthy: {str(e)}"
        
    try:
        await cache.ping()
        status["redis"] = "healthy"
    except Exception as e:
        status["redis"] = f"unhealthy: {str(e)}"

    if any("unhealthy" in str(v) for v in status.values()):
        raise HTTPException(status_code=503, detail=status)
        
    return status

app.include_router(monitors.router, prefix=f"{settings.API_V1_STR}/monitors", tags=["monitors"])
