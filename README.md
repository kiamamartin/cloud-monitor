#  Cloud-Native API Performance & Uptime Monitor

A highly scalable, lightweight observability platform engineered to continuously monitor the health, availability, latency, and SLA compliance of APIs and web endpoints. 

Designed with enterprise **Site Reliability Engineering (SRE)** principles, this system decouples heavy database writes from high-speed API reads using a distributed caching layer, asynchronous workers, and Prometheus metrics.

---

## Architecture Highlights

- **Asynchronous Probing Engine:** Utilizes `FastAPI`, `asyncio`, and `httpx` to probe dozens of endpoints concurrently without thread-blocking.
- **Cache-Aside Pattern:** Metrics are persisted in **PostgreSQL** for historical data while simultaneously pushed to **Redis**. The API serves sub-millisecond responses directly from memory.
- **Distributed Rate Limiting:** API endpoints are protected against DDoS and abuse via a Redis-backed Fixed-Window token bucket algorithm.
- **Observability-Driven UI:** Exposes native Prometheus metrics for both API traffic and Worker latency, visualized in real-time via **Grafana**.
- **DevOps Ready:** Fully containerized with Docker, thoroughly linted (`ruff`), automatically tested (`pytest` / GitHub Actions), and includes Kubernetes (`k8s`) deployment manifests.

---

## 1.System Architecture

```text
                +----------------------+
                |    Client / Curl     |
                +----------+-----------+
                           |
                           v
              +------------+-------------+
              |       FastAPI API        | (Rate Limited via Redis)
              +------+-----------+-------+
                     |           |
             Cache Reads     Fallback Read
                     |           |
                     v           v
               +-----------+ +-----------+
               |   Redis   | | Postgres  |
               +-----------+ +-----------+
                     ^           ^
               Cache Write   Store Result
                     |           |
              +------+-----------+-------+
              |   Async Python Worker    | (Probes endpoints)
              +----------+-----------+---+
                         |
                         v
                [ Target Websites/APIs ]

# Cloud-Native API Performance & Uptime Monitor

## Technology Stack

* **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (Async)
* **Data Layer:** PostgreSQL 15, Redis 7, Alembic (Async Migrations)
* **Observability:** Prometheus, Grafana, prometheus-client
* **Infrastructure:** Docker Compose, Kubernetes, GitHub Actions CI/CD

---

#  Setup Guide (Docker Production Mode - Recommended)

The easiest way to run the entire stack (API, Worker, Postgres, Redis, Prometheus, Grafana) is via Docker Compose.

## 1. Clone the Repository

```bash
git clone https://github.com/yourusername/cloud-monitor.git
cd cloud-monitor
```

## 2. Start the Stack

```bash
docker compose up --build -d
```

## 3. Access the Services

| Service                            | URL                        |
| ---------------------------------- | -------------------------- |
| FastAPI Interactive Docs (Swagger) | http://localhost:8000/docs |
| Grafana Dashboards                 | http://localhost:3000      |
| Prometheus Metrics (Raw)           | http://localhost:9090      |

**Grafana Default Credentials**

```text
Username: admin
Password: admin
```

---

#  Setup Guide (Local Development Mode)

If you want to actively develop the application, run PostgreSQL, Redis, Prometheus, and Grafana in Docker while running FastAPI and the monitoring worker locally.

## 1. Start Infrastructure Services

```bash
docker compose up postgres redis prometheus grafana -d
```

## 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Run Database Migrations

```bash
alembic upgrade head
```

## 4. Start the FastAPI Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 5. Start the Monitoring Worker

Open a new terminal and run:

```bash
source venv/bin/activate
python -m app.workers.monitor_worker
```

---

#  Troubleshooting & Debugging

## 1. `[Errno 111] Connection Refused` to Postgres/Redis

### Cause

On many Linux distributions (Fedora, Ubuntu, etc.), `localhost` may resolve to the IPv6 loopback address (`::1`) while Docker exposes services on IPv4 (`127.0.0.1`).

### Fix

Update your environment variables:

```env
DATABASE_URL=postgresql+asyncpg://monitor_user:monitor_password@127.0.0.1:5432/cloud_monitor
REDIS_URL=redis://127.0.0.1:6379/0
```

---

## 2. Docker TLS Handshake Timeout

### Cause

Temporary routing or network latency when communicating with Docker Hub.

### Fix

```bash
docker compose pull
docker compose up -d
```

---

## 3. Monitors Returning Status `0`

### Cause

A status of `0` indicates the HTTP connection terminated before receiving a response. This often occurs when:

* SSL verification fails.
* A target site blocks requests without a browser-like User-Agent.
* Reverse proxies such as Cloudflare reject automated requests.

### Fix

Ensure `app/services/prober.py`:

* Sets a browser-style `User-Agent` header.
* Configures `verify=False` in `httpx.AsyncClient` when appropriate.

---

## 4. `sqlalchemy.exc.IllegalStateChangeError`

### Error

```text
Method 'commit()' can't be called here
```

### Cause

SQLAlchemy sessions are not thread-safe. Sharing one session across multiple concurrent tasks can cause transaction conflicts.

### Fix

Create an isolated database session within each task:

```python
async with AsyncSessionLocal() as db:
    ...
```

---

## 5. `ModuleNotFoundError: No module named 'app'`

### Cause

Running Python files directly bypasses proper package resolution.

### Incorrect

```bash
python app/workers/monitor_worker.py
```

### Correct

```bash
python -m app.workers.monitor_worker
```

---

# API Usage

## Create a New Monitor

```bash
curl -X POST http://localhost:8000/api/v1/monitors/ \
  -H "Content-Type: application/json" \
  -d '{
        "name": "GitHub",
        "url": "https://github.com",
        "interval_seconds": 15
      }'
```

> The monitoring worker automatically discovers newly created monitors from the database during its next polling cycle. No restart is required.

---

## Fetch Real-Time Status

```bash
curl http://localhost:8000/api/v1/monitors/{monitor_id}/status
```

This endpoint serves status data directly from Redis, providing near real-time responses with minimal latency.

---

#  Grafana Dashboard Setup

Instead of maintaining a custom frontend, the platform leverages Grafana as an observability-driven user interface.

## Configure Prometheus Data Source

1. Open Grafana:

   ```text
   http://localhost:3000
   ```

2. Navigate to:

   ```text
   Connections → Data Sources
   ```

3. Add a new **Prometheus** data source.

4. Configure the URL:

### Docker Environment

```text
http://prometheus:9090
```

### Local Environment

```text
http://localhost:9090
```

---

## Recommended Dashboard Panels

### Global Uptime Grid

**PromQL Query**

```promql
monitor_uptime
```

**Visualization**

* Panel Type: Stat
* Calculation: Last Value

---

### Endpoint Latency Tracking

**PromQL Query**

```promql
monitor_latency_ms
```

**Visualization**

* Panel Type: Time Series

---

### API Backend Traffic

**PromQL Query**

```promql
rate(http_requests_total[1m])
```

**Visualization**

* Panel Type: Time Series

---

#  Future Enhancements

## Distributed Monitoring

* Multi-region monitoring agents
* Global latency comparison
* Edge-based health checks

## Advanced Alerting

* Slack integrations
* PagerDuty integrations
* Microsoft Teams notifications
* Escalation policies

## AI-Powered Analytics

* Latency anomaly detection
* Predictive outage analysis
* Automated SLA risk assessment

## SSL & Security Monitoring

* SSL certificate expiration tracking
* TLS configuration auditing
* Security header validation

## Reporting & Compliance

* Historical uptime reporting
* SLA compliance dashboards
* Exportable PDF and CSV reports
* Executive-level operational summaries

---

# Conclusion

The Cloud-Native API Performance & Uptime Monitor provides a lightweight yet scalable observability platform capable of monitoring endpoint availability, latency, and service health in real time. By combining FastAPI, PostgreSQL, Redis, Prometheus, Grafana, and containerized deployment strategies, the system delivers enterprise-grade monitoring capabilities while remaining simple to deploy and maintain.
