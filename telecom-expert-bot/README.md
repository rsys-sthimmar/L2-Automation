# Telecommunications Expert AI Bot

A FastAPI-based AI assistant specialized in 3GPP telecommunications specifications (R15-R19).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐  │
│  │  /query  │  │/knowledge │  │  /logs   │  │/testplan │  │
│  └────┬─────┘  └─────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │              │        │
│  ┌────▼──────────────▼──────────────▼──────────────▼─────┐ │
│  │              Services Layer                            │ │
│  │  LLMService  KnowledgeService  LogAnalyzer  TestPlan  │ │
│  └────┬─────────────────┬──────────────────────────────┘  │
│       │                 │                                  │
│  ┌────▼────┐      ┌──────▼──────┐                         │
│  │ OpenAI  │      │  ChromaDB   │  ┌──────────────────┐   │
│  │  / Azure│      │ Vector Store│  │  SQLite (async)  │   │
│  └─────────┘      └─────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone and enter directory
cd telecom-expert-bot

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# 5. Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Open API docs
# http://localhost:8000/docs
```

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /health | Health check | None |
| POST | /auth/register | Register user | None |
| POST | /auth/login | Login | None |
| GET | /auth/me | Current user | Bearer |
| POST | /query | Ask telecom question | Bearer |
| GET | /knowledge | List knowledge items | Bearer |
| POST | /knowledge | Create knowledge item | Bearer |
| GET | /knowledge/{id} | Get knowledge item | Bearer |
| PUT | /knowledge/{id} | Update knowledge item | Bearer |
| DELETE | /knowledge/{id} | Delete knowledge item | Master |
| POST | /knowledge/{id}/approve | Approve item | Master |
| POST | /knowledge/{id}/reject | Reject item | Master |
| POST | /logs/analyze | Analyze telecom logs | Bearer |
| POST | /testplan/generate | Generate test plan | Bearer |
| GET | /admin/users | List all users | Master |
| DELETE | /admin/users/{id} | Delete user | Master |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| APP_NAME | telecom-expert-bot | Application name |
| DATABASE_URL | sqlite+aiosqlite:///./telecom_bot.db | Database connection |
| LLM_PROVIDER | openai | LLM provider (openai/azure) |
| OPENAI_API_KEY | - | OpenAI API key |
| OPENAI_MODEL | gpt-4 | OpenAI model name |
| AZURE_OPENAI_API_KEY | - | Azure OpenAI key |
| AZURE_OPENAI_ENDPOINT | - | Azure endpoint URL |
| CHROMA_PERSIST_DIRECTORY | ./chroma_data | ChromaDB data directory |
| JWT_SECRET_KEY | change-me | JWT signing key |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | 1440 | Token expiry (24h) |

## User Roles

| Role | Permissions |
|------|-------------|
| **master** | Full access: create/approve/reject/delete knowledge, manage users, all queries |
| **child** | Query, create knowledge (pending approval), view confirmed knowledge |

## Knowledge Workflow

```
Child User Creates → [pending] → Master Approves → [confirmed]
                               → Master Rejects  → [rejected]
Master User Creates → [confirmed] (auto-approved)
```

## Example API Calls

```bash
# Register a master user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@example.com","password":"secret","role":"master"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"secret"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

# Ask a telecom question
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"Explain RRC Setup procedure with message flow","domain":"RRC"}'

# Analyze logs
curl -X POST http://localhost:8000/logs/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"log_text":"2024-01-01 10:00:00 [INFO] RRCSetup sent\n2024-01-01 10:00:01 [ERROR] RRCSetupComplete timeout"}'

# Generate test plan
curl -X POST http://localhost:8000/testplan/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"feature":"Handover","domain":"RRC","requirements":["Handover latency < 50ms"]}'
```

## Running Tests

```bash
pytest tests/ -v --tb=short
```

## Docker

```bash
docker-compose up --build
```

## Supported 3GPP Domains

| Domain | Specification | Description |
|--------|--------------|-------------|
| RRC | TS 38.331 | Radio Resource Control |
| NGAP | TS 38.413 | NG Application Protocol |
| F1AP | TS 38.473 | F1 Application Protocol |
| MAC | TS 38.321 | Medium Access Control |
| PHY | TS 38.211 | Physical Channels |
| NTN | TS 38.821 | Non-Terrestrial Networks |
| PDCP | TS 38.323 | Packet Data Convergence |
| RLC | TS 38.322 | Radio Link Control |
| 5GC | TS 23.501 | 5G Core Architecture |
