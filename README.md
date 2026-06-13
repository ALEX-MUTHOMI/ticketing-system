# Ticketing System

Multi-company event ticketing platform with checkout holds, payments (LemonSqueezy + M-Pesa), QR check-in, refunds, and settlements.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Cloudflare Edge                         │
│   WAF · DDoS · Rate Limiting · Turnstile · Cache Rules     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Nginx (TLS termination)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Django REST Framework (Gunicorn)                │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │companies │ │  events  │ │inventory │ │   checkout   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ tickets  │ │ checkin  │ │ payments │ │   webhooks   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │accounts  │ │  audit   │ │  celery  │ │     core     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
└──────┬──────────────────────────────────────┬──────────────┘
       │                                      │
┌──────▼──────┐                    ┌──────────▼──────────┐
│ PostgreSQL  │                    │    Redis            │
│ (primary)   │                    │ (cache + Celery)    │
└─────────────┘                    └─────────────────────┘
```

## Data Structures & Algorithms

Every DS&A choice solves a real production problem:

| Structure | Module | Problem Solved | Complexity |
|-----------|--------|---------------|------------|
| **Hash Map** | `checkout/hold_registry.py` | O(1) hold lookup under 1000 concurrent reservations | O(1) get/set |
| **Hash Map** | `payments/idempotency_store.py` | Deduplicate duplicate payment webhooks | O(1) lookup |
| **Hash Map** | `checkin/scan_registry.py` | O(1) QR fingerprint → TicketID validation | O(1) lookup |
| **Hash Map** | `companies/slug_index.py` | O(1) company resolution per request | O(1) lookup |
| **Min-Heap** | `checkout/expiry_heap.py` | Find earliest expiring hold in O(log N) | O(log N) push/pop |
| **LRU Cache** | `events/lru_cache.py` | O(1) hot event reads with bounded memory | O(1) read/evict |
| **Bloom Filter** | `checkin/bloom_guard.py` | Probabilistic O(1) duplicate scan detection before DB | O(1) check |
| **Binary Search** | `inventory/tier_selector.py` | O(log N) best-tier selection by budget | O(log N) |
| **Sliding Window** | `core/rate_limiter.py` | O(1) amortised rate limiting per IP/user | O(1) amortised |

### O(N) Bottlenecks We Actively Prevent

- Missing `company_id` index → full table scan on every tenant query → **fixed: composite index**
- Serializer N+1 on nested relations → **fixed: `select_related` / `prefetch_related`**
- Hold expiry `filter(expires_at__lt=now)` → full scan → **fixed: Redis sorted set O(log N)**
- QR lookup without index → **fixed: unique index on `fingerprint`**

## Security Model

### Attacker Surface — Smallest to Largest

| # | Attack | Defense |
|---|--------|---------|
| 1 | QR forgery | HMAC-SHA256 signed fingerprint — unforgeable without server secret |
| 2 | Hold abuse — starve inventory | Max 2 holds/user/event + sliding window rate limit + Celery expiry |
| 3 | Payment replay | Idempotency hash map: `payment_id → result` — O(1) dedup |
| 4 | Race on last ticket | `SELECT FOR UPDATE` row lock + atomic inventory decrement |
| 5 | Tenant isolation bypass | Every queryset filtered by `company_id` from JWT claim |
| 6 | Refund after check-in | Check-in status gate before refund authorisation |
| 7 | JWT role elevation | Roles re-fetched from DB on every request — token claim not trusted |
| 8 | Mass assignment | Explicit serializer allowlists — no `Meta.fields = "__all__"` |
| 9 | Webhook impersonation | HMAC signature verification on every inbound webhook |
| 10 | Brute force login | Account lockout after 5 failed attempts — stored in Redis |
| 11 | O(N) query abuse | Index audit + `assert_max_queries` in CI |
| 12 | Cross-tenant data leak | Integration red-team test: 50 probes, all rejected, all audited |

## Payment Providers

### LemonSqueezy
- Checkout URL generation via LS Checkout API
- Webhook: `order_created` → verify `X-Signature` HMAC-SHA256 → issue ticket
- Idempotency: `order_id` prevents double-issue on webhook retry

### M-Pesa (Safaricom Daraja)
- STK Push: phone payment prompt via Daraja API
- Callback: IP allowlist (Safaricom ranges) + `ResultCode` + `CheckoutRequestID` verification
- Idempotency: `CheckoutRequestID` hash map

## CI/CD Pipeline

```
GitHub Actions:
  1. ruff check          → lint + format enforcement
  2. bandit -r .         → security static analysis
  3. detect-secrets scan → block any committed secrets
  4. pip-audit           → dependency CVE check
  5. docker-compose test → pytest --cov=. --cov-fail-under=80
  6. ZAP baseline scan   → OWASP passive security scan
  7. merge to staging    → deploy to staging + smoke tests
  8. merge to main       → deploy to production
```

## Branch Strategy

```
main        ← production. Requires PR + CI green + staging verification
staging     ← pre-production. Auto-deployed on merge from development
development ← daily work. All feature commits land here
```

## Running Locally

```bash
cp .env.example .env
docker-compose up -d
docker-compose exec app python manage.py migrate
docker-compose exec app python manage.py createsuperuser
```

## Running Tests

```bash
# Docker-isolated test environment
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Local (requires running Postgres + Redis)
pytest --cov=. --cov-report=html
```

## Stack

- **Runtime:** Python 3.12, Django 6, Django REST Framework
- **Database:** PostgreSQL 16
- **Cache / Queue:** Redis 7
- **Async:** Celery + Celery Beat
- **Auth:** JWT (RS256) + Argon2 password hashing
- **Payments:** LemonSqueezy, M-Pesa (Safaricom Daraja)
- **Security:** Cloudflare WAF + Turnstile, HMAC webhooks, Bloom filters
- **Observability:** structlog, Sentry (PII-scrubbed), request ID middleware
- **CI/CD:** GitHub Actions, Docker Compose, ZAP, ruff, bandit
