import asyncio
from sqlalchemy import select
from prometheus_client import start_http_server, Gauge

from app.core.database import AsyncSessionLocal
from app.models.schema import Monitor, MonitorResult
from app.services.prober import probe_endpoint
from app.cache.service import cache_monitor_status

# Define Prometheus Metrics
PROBE_UP = Gauge('monitor_uptime', '1 if website is up, 0 if down', ['monitor_name', 'url'])
PROBE_LATENCY = Gauge('monitor_latency_ms', 'Latency of the website in ms', ['monitor_name', 'url'])

async def process_monitor(monitor: Monitor):
    print(f"[{monitor.name}] Pinging {monitor.url}...")
    
    is_up, status_code, response_time = await probe_endpoint(
        url=monitor.url,
        method=monitor.method,
        timeout_ms=monitor.timeout_ms
    )
    
    print(f"[{monitor.name}] Result: UP={is_up}, Status={status_code}, Time={response_time}ms")
    
    # Update Prometheus Grafana Metrics instantly
    PROBE_UP.labels(monitor_name=monitor.name, url=monitor.url).set(1 if is_up else 0)
    PROBE_LATENCY.labels(monitor_name=monitor.name, url=monitor.url).set(response_time)
    
    checked_at = None
    
    async with AsyncSessionLocal() as db:
        result = MonitorResult(
            monitor_id=monitor.id,
            status_code=status_code,
            response_time_ms=response_time,
            is_up=is_up
        )
        db.add(result)
        await db.commit()
        await db.refresh(result)
        checked_at = result.checked_at

    cache_payload = {
        "monitor_id": str(monitor.id),
        "name": monitor.name,
        "url": monitor.url,
        "is_up": is_up,
        "status_code": status_code,
        "response_time_ms": response_time,
        "last_checked": str(checked_at) if checked_at else None
    }
    
    ttl = monitor.interval_seconds * 3
    await cache_monitor_status(str(monitor.id), cache_payload, ttl_seconds=ttl)

async def run_worker():
    print("Starting Monitoring Worker...")
    # Start Prometheus metrics server for the worker on port 8001
    start_http_server(8001)
    
    while True:
        active_monitors = []
        async with AsyncSessionLocal() as db:
            query = select(Monitor).where(Monitor.is_active == True)
            result = await db.execute(query)
            active_monitors = result.scalars().all()
            
        if not active_monitors:
            print("No active monitors found. Sleeping for 10 seconds...")
        else:
            tasks = [process_monitor(monitor) for monitor in active_monitors]
            await asyncio.gather(*tasks)
                
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_worker())
