# FastAPI Resume Optimizer Boilerplate

This is a production-ready FastAPI backend for analyzing resumes against job descriptions, calculating ATS and relevance scores, finding missing keywords, and automatically generating optimized resume rewrites using state-of-the-art LLMs.

## 📋 Project Overview

This boilerplate provides a production-ready FastAPI backend with:
- JWT Authentication (registration, login, logout, token refresh)
- File parsing (PDF/DOCX) with Supabase Storage integration
- AI-powered resume analysis using Groq (Llama 3) or Gemini LLMs via LangChain
- ATS compatibility scoring and analysis
- AI-powered resume rewriting/optimization
- PostgreSQL database with SQLAlchemy 2.0 + FastCRUD
- Alembic migrations
- Docker Compose setup for easy deployment
- Optional Redis caching
- Comprehensive test suite

## 📂 Project Structure

```
src/
├── app/
│   ├── api/v1/              # REST API Endpoints
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── users.py         # User profile management
│   │   ├── resume.py        # Resume upload & text extraction
│   │   ├── job_description.py # Job description handling
│   │   ├── analysis.py      # Analysis trigger endpoints
│   │   ├── ats.py           # ATS scoring endpoints
│   │   ├── rewrite.py       # AI-powered resume rewriting
│   │   └── files.py         # File download endpoints
│   ├── core/                # Configuration, security, database setup
│   ├── crud/                # FastCRUD database instances
│   ├── models/              # SQLAlchemy domain models
│   ├── schemas/             # Pydantic validation schemas
│   └── services/            # Business logic services
│       ├── chains/          # LangChain prompts & parsers
│       ├── analysis_service.py # Analysis pipeline orchestrator
│       ├── file_service.py    # PDF/DOCX parsers
│       ├── llm_service.py     # AI client factory
│       └── storage_service.py # Supabase operations
├── migrations/              # Alembic migration scripts
├── scripts/                 # Utility scripts
├── main.py                  # Application entry point
└── .env                     # Environment variables
```

## 🔧 Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Environment Setup
1. Clone the repository
2. Copy environment template:
   ```bash
   cp src/.env.example src/.env
   ```
3. Edit `src/.env` with your actual credentials:
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

### Running with Docker Compose (Recommended)
```bash
docker-compose up --build
# First time only: run migrations
docker-compose exec web uv run alembic upgrade head
```

API will be available at: http://127.0.0.1:8000
Interactive docs: http://127.0.0.1:8000/docs

### Local Development
```bash
# Create virtual environment
uv venv
source .venv/bin/activate
uv sync

# Run migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload
```

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

## 🔐 Security Features
- JWT-based authentication with access/refresh tokens
- Password hashing using bcrypt
- Token blacklisting for logout functionality
- Environment-based configuration
- Secure file handling with Supabase Storage
- Input validation using Pydantic models

## 🧠 AI/LLM Integration
- Supports both Groq (Llama 3) and Google Gemini
- Abstracted LLM service layer for easy provider switching
- LangChain integration for prompt chaining and parsing
- Structured output parsing for consistent AI responses
- Configurable LLM provider via environment variable

## 💾 Data Storage
- PostgreSQL as primary database with SQLAlchemy 2.0 async
- Alembic for database migrations
- FastCRUD for simplified CRUD operations
- Supabase Storage for file persistence (resumes, generated documents)
- Optional Redis caching layer

## 📁 File Handling
- Secure PDF and DOCX file parsing
- File validation and sanitization
- Original file preservation in Supabase Storage
- Dynamic generation of PDF/DOCX output files
- Automatic cleanup mechanisms

## 🔄 API Endpoints Summary
- **Authentication**: `/api/v1/auth/*` (register, login, refresh, logout)
- **Users**: `/api/v1/users/*` (profile management)
- **Resumes**: `/api/v1/resumes/*` (upload, text extraction)
- **Job Descriptions**: `/api/v1/job-descriptions/*` (create, manage)
- **Analysis**: `/api/v1/analysis/` (run ATS + relevance analysis)
- **Rewriting**: `/api/v1/rewrite/` (generate optimized resume)
- **ATS Scoring**: `/api/v1/ats/*` (quick ATS checks)
- **Files**: `/api/v1/files/download/*` (download generated files)

## 🛠️ Development Tools
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Pytest** with pytest-asyncio for testing
- **Pre-commit** hooks for code quality
- **Structlog** for structured logging

## 📚 Key Services
- **analysis_service.py**: Orchestrates the complete analysis pipeline
- **file_service.py**: Handles PDF/DOCX parsing and text extraction
- **llm_service.py**: Factory pattern for LLM provider abstraction
- **storage_service.py**: Abstracts Supabase Storage operations
- **chains/**: Contains LangChain prompts and output parsers

## 🔄 Database Migrations
Using Alembic for schema management:
```bash
# Generate new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

## 🐳 Docker Details
Multi-stage build:
1. **Builder stage**: Uses astral-sh/uv for fast dependency installation
2. **Final stage**: Slim Python image with non-root user for security
3. Environment variables passed at runtime
4. Volume mounts for persistent data (if needed)

## 🧪 Testing Strategy
- Unit tests for individual components
- Integration tests for API endpoints
- Test database isolation
- Mock external services (Supabase, LLMs) where appropriate
- Async test support with pytest-asyncio

## 📝 Environment Variables Reference
See `src/.env.example` for complete reference. Key categories:
- **Database**: PostgreSQL connection settings
- **Security**: JWT secret, algorithm, expiration
- **Storage**: Supabase URL, service key, bucket name
- **LLM**: Provider selection and API keys
- **Caching**: Redis configuration (optional)
- **Server**: Host, port, reload settings

## 🔄 Background Processing Note
Currently, analysis operations are synchronous for simplicity. For production workloads, consider integrating:
- Celery/ARQ for background job processing
- WebSocket progress updates
- Job queuing with retry mechanisms

## 🔮 Future Enhancements
- Stripe integration for monetization
- Webhooks for Supabase storage events
- Expanded LLM provider options
- Advanced analytics and dashboard
- User subscription tiers
- Batch processing capabilities

--- 
*This CLAUDE.md provides guidance for Claude Code when working with this codebase.*