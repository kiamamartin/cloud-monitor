import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List

from app.core.database import get_db
from app.models.schema import Monitor, MonitorResult, User
from app.schemas.monitor import MonitorCreate, MonitorResponse
from app.cache.service import get_cached_monitor_status, cache_monitor_status
from app.rate_limit.limiter import RateLimiter

router = APIRouter()
limiter = RateLimiter(requests_per_minute=20) # Bumped to 20 for testing

@router.post("/", response_model=MonitorResponse, status_code=201)
async def create_monitor(monitor_in: MonitorCreate, db: AsyncSession = Depends(get_db)):
    """Create a new endpoint monitor."""
    
    # Quick hack: Grab the first user in the DB since we don't have JWT auth wired up yet
    user_query = select(User).limit(1)
    user = (await db.execute(user_query)).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=500, detail="No users found in database to assign monitor.")

    new_monitor = Monitor(
        user_id=user.id,
        name=monitor_in.name,
        url=str(monitor_in.url),
        method=monitor_in.method,
        interval_seconds=monitor_in.interval_seconds,
        timeout_ms=monitor_in.timeout_ms
    )
    
    db.add(new_monitor)
    await db.commit()
    await db.refresh(new_monitor)
    
    return new_monitor

@router.get("/", response_model=List[MonitorResponse])
async def list_monitors(db: AsyncSession = Depends(get_db)):
    """List all configured monitors."""
    query = select(Monitor).where(Monitor.is_active == True)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{monitor_id}/status", dependencies=[Depends(limiter)])
async def get_monitor_status(monitor_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Any:
    """Get the real-time status of a specific monitor."""
    monitor_id_str = str(monitor_id)
    
    cached_data = await get_cached_monitor_status(monitor_id_str)
    if cached_data:
        cached_data["source"] = "redis_cache"
        return cached_data

    query = select(Monitor).where(Monitor.id == monitor_id)
    result = await db.execute(query)
    monitor = result.scalar_one_or_none()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found in Database")

    res_query = select(MonitorResult).where(
        MonitorResult.monitor_id == monitor_id
    ).order_by(MonitorResult.checked_at.desc()).limit(1)
    
    latest_result = (await db.execute(res_query)).scalar_one_or_none()
    
    response_data = {
        "monitor_id": monitor_id_str,
        "name": monitor.name,
        "url": monitor.url,
        "is_up": latest_result.is_up if latest_result else None,
        "status_code": latest_result.status_code if latest_result else None,
        "response_time_ms": latest_result.response_time_ms if latest_result else None,
        "last_checked": str(latest_result.checked_at) if latest_result else None,
        "source": "postgresql_database"
    }

    await cache_monitor_status(monitor_id_str, response_data, ttl_seconds=monitor.interval_seconds * 3)
    return response_data
