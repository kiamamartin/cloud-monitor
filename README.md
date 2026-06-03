# Cloud-Native API Performance & Uptime Monitor

A highly scalable, cloud-native observability platform engineered to continuously monitor the health, availability, latency, and SLA compliance of APIs and web endpoints. 

Designed with enterprise SRE (Site Reliability Engineering) principles, this system decouples heavy database writes from high-speed API reads using a distributed caching layer and asynchronous workers.

## Architecture Highlights

- **Asynchronous Engine:** Utilizes `FastAPI`, `asyncio`, and `httpx` to probe dozens of endpoints concurrently without thread-blocking.
- **Cache-Aside Pattern:** Metrics are persisted in **PostgreSQL** for historical data while simultaneously pushed to **Redis**. The API serves sub-millisecond responses directly from memory.
- **Distributed Rate Limiting:** API endpoints are protected against DDoS and abuse via a Redis-backed Fixed-Window token bucket algorithm.
- **Observability-Driven UI:** Exposes native Prometheus metrics for both API traffic and Worker latency, visualized in real-time via **Grafana**.
- **DevOps Ready:** Fully containerized with Docker, thoroughly linted (`ruff`), automatically tested (`pytest` / GitHub Actions), and includes Kubernetes (`k8s`) deployment manifests.

##  Technology Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (Async)
- **Data Layer:** PostgreSQL 15, Redis 7, Alembic (Async Migrations)
- **Observability:** Prometheus, Grafana
- **Infrastructure:** Docker Compose, Kubernetes, GitHub Actions CI/CD

##  Quick Start Docker Compose

The entire stack (API, Worker, Postgres, Redis, Prometheus, Grafana) can be spun up with a single command:

```bash
git clone https://github.com/yourusername/cloud-monitor.git
cd cloud-monitor
docker compose up --build -d