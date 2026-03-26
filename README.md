# DCDeepTech API Gateway

Production-style FastAPI backend for the DCDeepTech AI API platform.

OpenAI-compatible proxy gateway with user management, API key auth, per-request billing, and usage logging.

---

## Architecture

```
Client / SDK
    │
    ▼
FastAPI (api.dcdeeptech.com)
    │
    ├── Auth (JWT)           POST /auth/register | /auth/login
    ├── API Key CRUD         GET|POST|DELETE /v1/keys
    ├── Model catalog        GET /v1/models
    ├── Usage log            GET /v1/usage
    ├── Billing/wallet       GET /v1/billing/wallet | /transactions
    ├── Admin                /admin/*
    └── OpenAI Proxy ──────► OpenRouter / vLLM / Custom
            │
            ▼
        usage_log + wallet debit (per request)
```

---

## Quick Start (Local Development)

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 15+ running locally
- (Optional) Docker for Postgres

### 2. Clone and set up environment

```bash
git clone <repo>
cd dcdeeptech-api

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Key | Description |
|-----|-------------|
| `SECRET_KEY` | Random 32+ char string — `openssl rand -hex 32` |
| `DATABASE_URL` | Your PostgreSQL async URL |
| `OPENROUTER_API_KEY` | Your OpenRouter API key from openrouter.ai |

### 4. Create database and run migrations

```bash
# Create the database (if it doesn't exist)
psql -U postgres -c "CREATE DATABASE dcdeeptech;"

# Run Alembic migrations (creates all tables + seeds model catalog)
alembic upgrade head
```

### 5. Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now live at **http://localhost:8000**

Interactive docs: **http://localhost:8000/docs**

---

## API Walkthrough

### Register a user

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword","full_name":"Your Name"}'
```

### Login and get JWT

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'

# → {"access_token":"eyJ...","token_type":"bearer"}
```

### Create an API key

```bash
curl -X POST http://localhost:8000/v1/keys \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Production Key"}'

# → {"key":"dcdt_sk_live_...","key_prefix":"dcdt_sk_live_xxxx",...}
# Store the full key securely — it is NOT retrievable after this.
```

### Top up wallet (admin only)

```bash
curl -X POST http://localhost:8000/admin/wallets/<user_id>/adjust \
  -H "Authorization: Bearer <ADMIN_JWT>" \
  -H "Content-Type: application/json" \
  -d '{"amount":10.00,"type":"topup","description":"Initial credit"}'
```

### Make a chat completion (OpenAI SDK compatible)

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dcdt_sk_live_your_key_here"
)

response = client.chat.completions.create(
    model="claude-3-5-sonnet",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

Or via curl:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer dcdt_sk_live_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## Creating an Admin User

After registering normally, update the role directly in the DB:

```sql
UPDATE users SET role = 'admin' WHERE email = 'admin@yourcompany.com';
```

---

## Project Structure

```
dcdeeptech-api/
├── app/
│   ├── main.py               # FastAPI app, routers, CORS
│   ├── core/
│   │   ├── config.py         # Pydantic settings from .env
│   │   ├── database.py       # Async SQLAlchemy engine + session
│   │   ├── security.py       # JWT + bcrypt
│   │   └── deps.py           # FastAPI dependencies (auth, roles)
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic v2 request/response schemas
│   ├── api/                  # FastAPI routers (thin — business logic in services)
│   ├── services/             # Business logic layer
│   ├── adapters/             # Provider adapters (OpenRouter, vLLM)
│   └── utils/                # idgen, time, masking helpers
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_initial_schema.py
├── alembic.ini
├── requirements.txt
└── .env.example
```

---

## Adding a New AI Provider

1. Create `app/adapters/myprovider_adapter.py` extending `BaseAdapter`
2. Implement `async def chat_completion(upstream_model, payload) -> dict`
3. Add enum value to `ModelProvider` in `app/models/model_catalog.py`
4. Register adapter in `app/services/provider_router.py`
5. Add models to catalog via `POST /admin/models`

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | DCDeepTech API Gateway | Display name |
| `APP_ENV` | development | `development` or `production` |
| `SECRET_KEY` | — | JWT signing key (required) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | JWT lifetime |
| `DATABASE_URL` | — | PostgreSQL async URL (required) |
| `CORS_ORIGINS` | http://localhost:5173 | Comma-separated allowed origins |
| `OPENROUTER_API_KEY` | — | OpenRouter key (required for proxy) |
| `OPENROUTER_BASE_URL` | https://openrouter.ai/api/v1 | Override for testing |
| `DEFAULT_CURRENCY` | USD | Wallet currency |

---

## Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "add column xyz"

# Roll back one step
alembic downgrade -1
```

---

## Security Notes

- Passwords are hashed with bcrypt (never stored or logged in plaintext)
- API keys are stored as bcrypt hashes — the plaintext is shown once at creation
- JWT tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES`
- Admin endpoints check `role == admin` via dependency injection
- CORS is restricted to configured origins
- `SELECT FOR UPDATE` prevents wallet overdraft race conditions
