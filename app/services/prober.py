import time
import httpx
from typing import Tuple

async def probe_endpoint(url: str, method: str = "GET", timeout_ms: int = 5000) -> Tuple[bool, int, float]:
    timeout_seconds = timeout_ms / 1000.0
    start_time = time.perf_counter()
    
    # Disguise our prober as a legitimate browser/monitoring agent
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CloudMonitor/1.0; +https://github.com/monitor)",
        "Accept": "*/*",
    }
    
    try:
        # verify=False ignores SSL cert errors (we just want to know if it responds)
        # follow_redirects=True ensures we get to the final destination
        async with httpx.AsyncClient(timeout=timeout_seconds, verify=False, follow_redirects=True) as client:
            response = await client.request(method, url, headers=headers)
            
            end_time = time.perf_counter()
            response_time_ms = (end_time - start_time) * 1000
            
            is_up = 200 <= response.status_code < 400
            return is_up, response.status_code, round(response_time_ms, 2)
            
    except httpx.TimeoutException:
        return False, 408, float(timeout_ms)
    except Exception as e:
        # Catch DNS, network drops, or other low-level errors and print them
        print(f"[{url}] Network Error: {type(e).__name__} - {str(e)}")
        return False, 0, 0.0
