# VeriTruth AI — Multi-Layer Fake News Intelligence System

> An enterprise-grade, full-stack platform that combines **8 AI analysis layers** to detect misinformation, propaganda, sentiment manipulation, and deepfake media — built for students, educators, researchers, and journalists.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Features](#features)
4. [Project Structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Quick Start (Docker)](#quick-start-docker)
7. [Local Development](#local-development)
8. [Environment Variables](#environment-variables)
9. [API Documentation](#api-documentation)
10. [AI Pipeline](#ai-pipeline)
11. [Database Schema](#database-schema)
12. [Deployment](#deployment)
13. [Contributing](#contributing)
14. [License](#license)

---

## Architecture Overview

```
┌──────────────┐       ┌─────────────┐       ┌──────────────────┐
│   Next.js    │◄─────►│   Nginx     │◄─────►│  FastAPI (REST)  │
│   Frontend   │  WS   │   Reverse   │       │  + WebSocket     │
│   (React 18) │◄─────►│   Proxy     │       │                  │
└──────────────┘       └─────────────┘       └────────┬─────────┘
                                                      │
                                  ┌───────────────────┼───────────────────┐
                                  │                   │                   │
                            ┌─────▼─────┐       ┌─────▼─────┐     ┌──────▼──────┐
                            │ PostgreSQL │       │  MongoDB   │     │   Neo4j     │
                            │ (users,    │       │ (results,  │     │ (knowledge  │
                            │  analyses) │       │  labels)   │     │  graph)     │
                            └───────────┘       └───────────┘     └─────────────┘
                                                      │
                                               ┌──────▼──────┐
                                               │    Redis     │
                                               │ (cache, pub/ │
                                               │  sub, queue) │
                                               └──────┬──────┘
                                                      │
                                               ┌──────▼──────┐
                                               │   Celery     │
                                               │  Worker +    │
                                               │  Beat        │
                                               └─────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, Framer Motion, Zustand, TanStack Query, D3.js, Chart.js, Radix UI |
| **Backend** | FastAPI, Python 3.11, Pydantic v2, SQLAlchemy 2 (async), Motor, Neo4j async driver |
| **AI/ML** | HuggingFace Transformers (RoBERTa, DeBERTa, BERT), spaCy, SHAP, OpenAI GPT, torchvision (EfficientNet) |
| **Databases** | PostgreSQL 16, MongoDB 7, Neo4j 5, Redis 7 |
| **Task Queue** | Celery 5 with Redis broker + periodic beat scheduler |
| **Infrastructure** | Docker Compose, Nginx, GitHub Actions CI/CD |
| **Auth** | JWT (access + refresh tokens), bcrypt, Google OAuth2, role-based access control |

## Features

- **8-Layer AI Analysis Pipeline** — fake-news classifier, claim extraction, fact verification, propaganda detection, sentiment analysis, deepfake detection, credibility scoring, knowledge graph generation
- **Real-time Progress** — WebSocket-powered live updates during analysis
- **Interactive Knowledge Graph** — D3.js force-directed graph showing entity relationships
- **Explainability (XAI)** — SHAP-based token attribution and suspicious passage highlighting
- **5-Role RBAC** — student, educator, researcher, journalist, admin
- **Browser Extension API** — quick-check endpoint for upcoming Chrome extension
- **Community Training Labels** — user-submitted labels with admin approval workflow
- **Trusted Source Management** — admin CRUD for domain credibility database
- **Dark Theme UI** — glass-morphism design with VeriTruth brand palette

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── ai_models/          # 8 AI service modules
│   │   ├── auth/               # JWT + Google OAuth dependencies
│   │   ├── core/               # Config, database, security
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── routers/            # API route handlers
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Cache, analysis, source services
│   │   ├── worker/             # Celery app, tasks
│   │   └── main.py             # FastAPI entry point
│   ├── alembic/                # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js App Router pages
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom hooks (WebSocket)
│   │   ├── lib/                # API client, types, utils
│   │   └── store/              # Zustand state stores
│   ├── Dockerfile
│   └── package.json
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── .github/workflows/ci.yml
└── README.md
```

## Prerequisites

- **Docker** ≥ 24 & **Docker Compose** ≥ 2.20
- *Or* for local dev: Python 3.11+, Node.js 20+, PostgreSQL 16, MongoDB 7, Neo4j 5, Redis 7

## Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/veritruth-ai.git
cd veritruth-ai

# 2. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys (OPENAI_API_KEY, GOOGLE_FACT_CHECK_API_KEY)

# 3. Build & start all services
docker compose up --build -d

# 4. Run database migrations
docker compose exec api alembic upgrade head

# 5. Open the app
#    Frontend:  http://localhost
#    API docs:  http://localhost/docs
#    Neo4j UI:  http://localhost:7474
```

All 8 services (PostgreSQL, MongoDB, Neo4j, Redis, API, Celery Worker, Celery Beat, Nginx + Frontend) will start with health-check dependencies.

## Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Start databases (if not using Docker)
# Ensure PostgreSQL, MongoDB, Neo4j, Redis are running locally

# Configure
cp .env.example .env
# Edit .env with local connection strings

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --port 8000

# In a separate terminal — start Celery worker
celery -A app.worker.celery_app worker --loglevel=info -Q default,analysis,maintenance

# In a separate terminal — start Celery beat
celery -A app.worker.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# → http://localhost:3000
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://...` |
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | MongoDB database name | `veritruth` |
| `NEO4J_URI` | Neo4j Bolt URI | `bolt://localhost:7687` |
| `NEO4J_USER` / `NEO4J_PASSWORD` | Neo4j credentials | `neo4j` / `password` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | **required** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `OPENAI_API_KEY` | OpenAI API key for fact verification | optional |
| `GOOGLE_FACT_CHECK_API_KEY` | Google Fact Check API key | optional |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth2 credentials | optional |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:3000"]` |
| `ENVIRONMENT` | `development` or `production` | `development` |

See `backend/.env.example` for a complete template.

## API Documentation

Once the API server is running:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/signup` | Register a new user |
| `POST` | `/api/auth/login` | Obtain access + refresh tokens |
| `POST` | `/api/auth/refresh` | Refresh access token |
| `POST` | `/api/analysis/text` | Submit text for analysis |
| `POST` | `/api/analysis/url` | Submit URL for analysis |
| `POST` | `/api/analysis/upload` | Upload file for analysis |
| `GET` | `/api/analysis/{id}` | Get analysis results |
| `GET` | `/api/analysis` | List user's analyses |
| `WS` | `/api/ws/analysis/{id}` | Real-time analysis progress |
| `POST` | `/api/extension/quick-check` | Browser extension quick check |
| `GET` | `/api/admin/stats` | Admin dashboard statistics |
| `GET` | `/api/admin/analytics` | Admin analytics data |

## AI Pipeline

Each analysis passes through **8 sequential stages** orchestrated by a Celery task:

| Stage | Module | Model / Method |
|-------|--------|---------------|
| 1. Classification | `classifier.py` | RoBERTa + DeBERTa ensemble with confidence calibration |
| 2. Claim Extraction | `claim_extractor.py` | spaCy NLP with dependency parsing + quote detection |
| 3. Fact Verification | `fact_verifier.py` | RAG: Google Fact Check API + trusted sources + OpenAI synthesis |
| 4. Propaganda Detection | `propaganda_detector.py` | 18 SemEval-2020 propaganda techniques via zero-shot classification |
| 5. Sentiment Analysis | `sentiment_analyzer.py` | BERT sentiment + emotion detection + manipulation flag scoring |
| 6. Explainability | built-in | SHAP token-level attribution for classifier decisions |
| 7. Credibility Scoring | `credibility_scorer.py` | 5-factor weighted score (source, content, evidence, cross-ref, historical) |
| 8. Knowledge Graph | `knowledge_graph.py` | Neo4j entity-relationship graph with D3.js-compatible output |

## Database Schema

### PostgreSQL (Relational)

- **users** — id, email, hashed_password, full_name, role, institution, is_active, oauth_provider, oauth_id, created_at, updated_at
- **analyses** — id, user_id (FK), source_type, source_url, title, content_hash, status, overall_score, fake_probability, credibility_score, claims (JSON), propaganda_techniques (JSON), sentiment_data (JSON), evidence_sources (JSON), processing_time, created_at, updated_at
- **trusted_sources** — id, domain, name, credibility_score, bias_label, category, sub-scores (JSON), last_verified, created_at

### MongoDB (Document)

- **analysis_results** — Full analysis payloads with all AI outputs and SHAP data
- **training_labels** — Community-submitted labels (content_hash, label, user_id, approved)

### Neo4j (Graph)

- **Entity nodes** — Claims, Sources, VerifiedFacts, DisputedFacts, People, Organizations
- **Relationships** — SUPPORTS, CONTRADICTS, MENTIONS, PUBLISHED_BY, RELATED_TO

## Deployment

### Production Checklist

1. **Change all secrets** — JWT_SECRET_KEY, database passwords, API keys
2. **Enable HTTPS** — Add SSL certificates to Nginx (update nginx.conf with ssl_certificate directives)
3. **Set CORS_ORIGINS** — Restrict to your production domain
4. **Scale workers** — Increase Celery concurrency or add replicas in docker-compose
5. **Enable backups** — Configure PostgreSQL pg_dump cron, MongoDB mongodump, Neo4j backup
6. **Monitoring** — Add Prometheus + Grafana or Datadog for metrics
7. **Log aggregation** — Configure structured logging to ELK or CloudWatch

### Scaling

```yaml
# Scale Celery workers
docker compose up -d --scale worker=3

# Scale API servers
docker compose up -d --scale api=2
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit changes: `git commit -m "feat: add my feature"`
4. Push: `git push origin feat/my-feature`
5. Open a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
