# AI-Powered Resume Relevance & ATS Optimizer

A production-ready FastAPI backend for analyzing resumes against job descriptions, calculating ATS and relevance scores, finding missing keywords, and automatically generating optimized resume rewrites using state-of-the-art LLMs.

## 🚀 Features

- **JWT Authentication**: Full registration, login, logout (token blacklisting), and refresh flows.
- **File Parsing & Storage**: Extract text from uploaded PDF and DOCX files securely, saving original files in Supabase Storage.
- **AI Relevance Scoring**: Uses Groq (Llama 3) or Gemini via LangChain to score resumes based on skill match and experience alignment (0-100).
- **ATS Compatibility**: Evaluates formatting, keyword density, and section structure, delivering an ATS score and actionable recommendations.
- **AI Resume Rewrite**: Generates a tailored, ATS-friendly resume rewrite specifically designed to pass filters for a target Job Description.
- **Dynamic File Generation**: Download the final AI-rewritten resume automatically in PDF or DOCX format.
- **Fast & Scalable**: Asynchronous operations, SQLAlchemy 2.0 with PostgreSQL, and optional Redis caching.

## ⚙️ Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (SQLAlchemy 2.0 async + FastCRUD)
- **Migrations**: Alembic
- **AI / LLMs**: LangChain, Groq (Llama 3 70B default), Google Gemini GenAI
- **Storage**: Supabase Storage
- **Security**: JWT & bcrypt
- **Other**: UUID, python-multipart, python-dotenv, structlog, etc.

## 📂 Folder Structure

```text
src/
├── app/
│   ├── api/v1/                # REST API Endpoints
│   │   ├── auth.py            # Login, register, token refresh
│   │   ├── users.py           # User profile management
│   │   ├── resume.py          # Resume upload & text extraction
│   │   ├── job_description.py # JD creation (text/upload)
│   │   ├── analysis.py        # Trigger Relevance/ATS analysis
│   │   ├── ats.py             # Quick ATS score checks & tips
│   │   ├── rewrite.py         # AI-powered resume restructuring
│   │   └── files.py           # Download optimized PDF/DOCX
│   ├── core/                  # Config, Security, Database setup
│   ├── crud/                  # FastCRUD DB instances
│   ├── models/                # SQLAlchemy Domain Models
│   ├── schemas/               # Pydantic validation schemas
│   └── services/              # Business Logic Services
│       ├── chains/            # LangChain prompts & parsers
│       ├── analysis_service.py # Orchestrator for pipelines
│       ├── file_service.py    # PDF/DOCX parsers
│       ├── llm_service.py     # AI client factory
│       └── storage_service.py # Supabase operations
├── .env                       # Environment Variables
├── main.py                    # Application entry point
├── alembic.ini                # Alembic configuration
└── migrations/                # Alembic migration scripts
```

## 🔧 Setup Instructions

### Prerequisites
- Python 3.11+
- PostgreSQL
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### 1. Installation
Clone the repo and configure your virtual environment:
```bash
uv venv
source .venv/bin/activate
uv sync
```

### 2. Environment Variables
Copy the provided example file to create your own configuration:
```bash
cp src/.env.example src/.env
```
Update `src/.env` with your actual keys (especially Supabase and LLM API keys). Default passwords and hostnames work for local Docker development.

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=resume_optimizer
SECRET_KEY=your_super_secret_jwt_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
SUPABASE_STORAGE_BUCKET=resumes
DEFAULT_LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key
```

### 3. Running with Docker Compose (Recommended)
The easiest way to run the application with its PostgreSQL database is using Docker Compose:
```bash
docker-compose up --build
```
On first startup, you need to run the database migrations inside the `web` container:
```bash
docker-compose exec web uv run alembic upgrade head
```
Your API will be running at `http://127.0.0.1:8000`. Access the interactive API documentation at `http://127.0.0.1:8000/docs`.

### 4. Running Locally (Without Docker)
If you prefer to run the application locally without Docker:
1. Ensure PostgreSQL is running locally (or update the `.env` file to point to your PostgreSQL instance).
2. Run the database migrations:
   ```bash
   cd src
   uv run alembic upgrade head
   ```
3. Start the development server:
   ```bash
   uv run uvicorn app.main:app --reload
   ```
The API will be available at `http://127.0.0.1:8000`.

### 5. Database Migrations (Separate Command)
You can manage migrations independently using Alembic:
```bash
# Generate a new migration after model changes
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback the last migration
uv run alembic downgrade -1
```

## 🌐 API Overview

- `POST /api/v1/auth/register`: Create account
- `POST /api/v1/auth/login`: Get JWT Access + Refresh token
- `POST /api/v1/resumes/upload`: Upload PDF/DOCX and parse text
- `POST /api/v1/job-descriptions/`: Paste or upload JD
- `POST /api/v1/analysis/`: Run AI score analysis (Relevance + ATS)
- `POST /api/v1/rewrite/`: Generate an optimized rewrite
- `GET /api/v1/files/download/{report_id}/resume`: Get the new resume

## 🔮 Future Improvements

- Add Celery/ARQ for background asynchronous job processing (currently analysis is synchronous to simplify deployment).
- Integrate Stripe for monetization limits per user.
- Add webhooks for Supabase storage cleanup synchronization.
- Expand LLM provider choice directly from the request payload.
- Add user subscription tiers and billing.
- Implement advanced analytics dashboard.

## 🛠️ Development Tools

- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Pytest** with pytest-asyncio for testing
- **Pre-commit** hooks for code quality
- **Structlog** for structured logging

## 🧪 Running Tests
```bash
uv run pytest
```

## 🐳 Deployment
The project includes Docker Compose for easy deployment:
- Uses `ghcr.io/astral-sh/uv:python3.11-bookworm-slim` as builder stage
- Production-ready Python slim image
- Non-root user for security
- Configurable via environment variables

## 📝 Environment Variables Reference
See `src/.env.example` for complete reference. Key categories:
- **Database**: PostgreSQL connection settings
- **Security**: JWT secret, algorithm, expiration
- **Storage**: Supabase URL, service key, bucket name
- **LLM**: Provider selection and API keys
- **Caching**: Redis configuration (optional)
- **Server**: Host, port, reload settings