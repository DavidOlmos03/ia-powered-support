# FastAPI Microservice Architecture Design

**Role:** Senior Backend Engineer (Python)
**Date:** 2026-01-22
**Project:** AI-Powered Support Co-Pilot - Python API Service
**Stack:** FastAPI + LangChain + Supabase + Pydantic

---

## 1. ARCHITECTURE OVERVIEW

### System Responsibilities
The FastAPI microservice is the **AI Processing Engine** responsible for:
1. Receiving ticket processing requests
2. Orchestrating LLM classification via LangChain
3. Updating ticket records in Supabase
4. Handling errors and retries
5. Providing observability metrics

### Design Principles
- **Single Responsibility:** Each module handles one concern
- **Dependency Injection:** Loose coupling via FastAPI's DI system
- **Fail-Safe Defaults:** Always return valid classification
- **Idempotency:** Same request = same result
- **Type Safety:** Strict typing with Pydantic and mypy
- **12-Factor App:** Configuration via environment variables

### Non-Functional Requirements
- **Latency:** p95 < 5 seconds (including LLM call)
- **Throughput:** 10 requests/second minimum
- **Availability:** 99% uptime (excluding platform downtime)
- **Error Rate:** < 1% unhandled exceptions
- **Type Coverage:** 100% with mypy strict mode

---

## 2. PROJECT STRUCTURE

```
python-api/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration management
│   ├── dependencies.py            # Dependency injection providers
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py          # API route definitions
│   │   │   └── endpoints/
│   │   │       ├── __init__.py
│   │   │       ├── health.py      # Health check endpoint
│   │   │       └── tickets.py     # Ticket processing endpoint
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── domain.py              # Domain models (Category, Sentiment enums)
│   │   ├── requests.py            # API request schemas
│   │   ├── responses.py           # API response schemas
│   │   └── database.py            # Database models (if using ORM)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── classifier.py          # LLM classification service
│   │   ├── supabase_client.py     # Supabase database client
│   │   └── prompt_builder.py      # Prompt construction logic
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py          # Custom exception classes
│   │   ├── logging.py             # Structured logging setup
│   │   ├── middleware.py          # Custom middleware
│   │   └── security.py            # API key validation
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py          # Custom validators
│       └── retry.py               # Retry logic utilities
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── unit/
│   │   ├── test_classifier.py
│   │   ├── test_supabase_client.py
│   │   └── test_prompt_builder.py
│   ├── integration/
│   │   └── test_api_endpoints.py
│   └── e2e/
│       └── test_full_flow.py
│
├── scripts/
│   ├── seed_database.py           # Database seeding
│   └── run_migrations.py          # Manual migrations if needed
│
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── Dockerfile                     # Container definition
├── docker-compose.yml             # Local development setup
├── .env.example                   # Environment variables template
├── pyproject.toml                 # Project metadata + tool configs
├── mypy.ini                       # Type checking configuration
├── pytest.ini                     # Test configuration
└── README.md                      # API documentation
```

### File Organization Rationale

**Layered Architecture:**
1. **API Layer** (`app/api/`): HTTP interface, request/response handling
2. **Service Layer** (`app/services/`): Business logic, external integrations
3. **Model Layer** (`app/models/`): Data structures, validation
4. **Core Layer** (`app/core/`): Cross-cutting concerns (logging, errors, security)
5. **Utils Layer** (`app/utils/`): Reusable helpers

**Separation of Concerns:**
- Routes define endpoints → Controllers handle requests → Services execute logic
- Models define schemas → Validators ensure correctness → Database handles persistence
- No direct database calls from routes (always through services)

---

## 3. DEPENDENCY MANAGEMENT

### Core Dependencies

```ini
# Production (requirements.txt)
fastapi==0.109.0              # Web framework
uvicorn[standard]==0.27.0     # ASGI server
pydantic==2.5.3               # Data validation
pydantic-settings==2.1.0      # Settings management

langchain==0.1.0              # LLM orchestration
langchain-openai==0.0.2       # OpenAI integration
langchain-community==0.0.10   # Community integrations

supabase==2.3.4               # Supabase client
postgrest==0.13.0             # PostgreSQL REST client

python-dotenv==1.0.0          # Environment variables
python-multipart==0.0.6       # Form data parsing

tenacity==8.2.3               # Retry logic
prometheus-client==0.19.0     # Metrics export
structlog==23.3.0             # Structured logging

# Development (requirements-dev.txt)
pytest==7.4.4                 # Testing framework
pytest-asyncio==0.23.3        # Async test support
pytest-cov==4.1.0             # Coverage reports
httpx==0.26.0                 # HTTP client for tests

mypy==1.8.0                   # Static type checker
ruff==0.1.13                  # Linter + formatter
black==23.12.1                # Code formatter
isort==5.13.2                 # Import sorter

pre-commit==3.6.0             # Git hooks
```

### Dependency Injection Strategy

FastAPI's built-in DI system for:
- Database connections (lifecycle management)
- LLM clients (singleton pattern)
- Configuration objects (app-level injection)
- Request-scoped dependencies (e.g., API key validation)

---

## 4. DATA MODELS & TYPE SYSTEM

### Domain Enums

**Category Enum:**
```python
from enum import Enum

class TicketCategory(str, Enum):
    TECNICO = "Técnico"
    FACTURACION = "Facturación"
    COMERCIAL = "Comercial"
```

**Sentiment Enum:**
```python
class TicketSentiment(str, Enum):
    POSITIVO = "Positivo"
    NEUTRAL = "Neutral"
    NEGATIVO = "Negativo"
```

### Request Models

**ProcessTicketRequest:**
```python
from pydantic import BaseModel, Field, UUID4, validator

class ProcessTicketRequest(BaseModel):
    ticket_id: UUID4 = Field(
        ...,
        description="UUID of the ticket to process"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Ticket content text"
    )

    @validator('description')
    def validate_description(cls, v: str) -> str:
        # Sanitize input (remove excessive whitespace, etc.)
        cleaned = ' '.join(v.split())
        if len(cleaned) < 10:
            raise ValueError("Description too short after cleaning")
        return cleaned
```

### Response Models

**ClassificationResult:**
```python
class ClassificationResult(BaseModel):
    category: TicketCategory
    sentiment: TicketSentiment
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Model confidence (0-1)"
    )
```

**ProcessTicketResponse:**
```python
class ProcessTicketResponse(BaseModel):
    success: bool
    ticket_id: UUID4
    classification: ClassificationResult
    processing_time_ms: int
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ticket_id": "123e4567-e89b-12d3-a456-426614174000",
                "classification": {
                    "category": "Técnico",
                    "sentiment": "Negativo",
                    "confidence_score": 0.89
                },
                "processing_time_ms": 1234,
                "message": "Ticket processed successfully"
            }
        }
```

**ErrorResponse:**
```python
class ErrorDetail(BaseModel):
    code: str = Field(..., description="Error code (e.g., VALIDATION_ERROR)")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused error")

class ErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ErrorDetail
    request_id: str = Field(..., description="Unique request identifier")
```

### Database Models

**SupabaseTicket:**
```python
from datetime import datetime

class SupabaseTicket(BaseModel):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    description: str
    category: Optional[TicketCategory]
    sentiment: Optional[TicketSentiment]
    processed: bool
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    processing_error: Optional[str]
    retry_count: int

    class Config:
        from_attributes = True  # Pydantic v2 ORM mode
```

---

## 5. API CONTRACT SPECIFICATION

### Endpoint: POST /api/v1/process-ticket

**Purpose:** Process a support ticket through LLM classification

**Authentication:** API Key (Header: `X-API-Key`)

**Request:**
```http
POST /api/v1/process-ticket HTTP/1.1
Host: api.example.com
Content-Type: application/json
X-API-Key: your-api-key-here

{
  "ticket_id": "123e4567-e89b-12d3-a456-426614174000",
  "description": "Mi conexión a internet no funciona desde hace 3 días"
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "ticket_id": "123e4567-e89b-12d3-a456-426614174000",
  "classification": {
    "category": "Técnico",
    "sentiment": "Negativo",
    "confidence_score": 0.89
  },
  "processing_time_ms": 1234,
  "message": "Ticket processed successfully"
}
```

**Response (Error - 400 Bad Request):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Description must be at least 10 characters",
    "field": "description"
  },
  "request_id": "req_abc123xyz"
}
```

**Response (Error - 422 Unprocessable Entity):**
```json
{
  "success": false,
  "error": {
    "code": "TICKET_NOT_FOUND",
    "message": "Ticket with ID 123e4567-... does not exist",
    "field": "ticket_id"
  },
  "request_id": "req_abc123xyz"
}
```

**Response (Error - 500 Internal Server Error):**
```json
{
  "success": false,
  "error": {
    "code": "LLM_SERVICE_ERROR",
    "message": "Failed to classify ticket after 3 retry attempts",
    "field": null
  },
  "request_id": "req_abc123xyz"
}
```

**Response (Error - 503 Service Unavailable):**
```json
{
  "success": false,
  "error": {
    "code": "DATABASE_UNAVAILABLE",
    "message": "Unable to connect to database",
    "field": null
  },
  "request_id": "req_abc123xyz"
}
```

### Additional Endpoints

**GET /health**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-22T10:30:00Z",
  "services": {
    "database": "up",
    "llm": "up"
  }
}
```

**GET /metrics** (Prometheus format)
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="POST",endpoint="/process-ticket",status="200"} 1234

# HELP api_request_duration_seconds API request duration
# TYPE api_request_duration_seconds histogram
api_request_duration_seconds_bucket{le="0.5"} 800
api_request_duration_seconds_bucket{le="1.0"} 950
```

---

## 6. SERVICE LAYER ARCHITECTURE

### ClassifierService

**Responsibility:** LLM-based ticket classification

**Interface:**
```python
class ClassifierService(Protocol):
    async def classify_ticket(
        self,
        description: str,
        *,
        max_retries: int = 3,
        timeout_seconds: float = 10.0
    ) -> ClassificationResult:
        """
        Classify ticket using LLM.

        Args:
            description: Ticket text content
            max_retries: Number of retry attempts on failure
            timeout_seconds: Maximum time to wait for LLM response

        Returns:
            ClassificationResult with category and sentiment

        Raises:
            LLMServiceError: If classification fails after retries
            LLMTimeoutError: If request exceeds timeout
        """
        ...
```

**Implementation Strategy:**
- LangChain ChatOpenAI or HuggingFace pipeline
- Structured output parsing with Pydantic
- Retry logic with exponential backoff (tenacity)
- Fallback to default values on parse errors
- Request timeout enforcement
- Token usage tracking

**Error Handling:**
- Rate limit errors → Exponential backoff
- Parse errors → Fallback to defaults (Técnico + Neutral)
- Timeout errors → Retry with shorter prompt
- Network errors → Retry with jitter

### SupabaseService

**Responsibility:** Database operations via Supabase client

**Interface:**
```python
class SupabaseService(Protocol):
    async def get_ticket(self, ticket_id: UUID) -> Optional[SupabaseTicket]:
        """Fetch ticket by ID"""
        ...

    async def start_processing(self, ticket_id: UUID) -> None:
        """Mark ticket as processing started"""
        ...

    async def complete_processing(
        self,
        ticket_id: UUID,
        classification: ClassificationResult
    ) -> SupabaseTicket:
        """Update ticket with classification results"""
        ...

    async def record_error(
        self,
        ticket_id: UUID,
        error_message: str
    ) -> None:
        """Record processing error"""
        ...

    async def health_check(self) -> bool:
        """Verify database connectivity"""
        ...
```

**Implementation Strategy:**
- Supabase Python client with service role key
- Connection pooling for performance
- Automatic retry on transient failures
- Query timeout configuration
- RLS bypass via service role

**Error Handling:**
- Connection errors → Retry 3x with backoff
- Timeout errors → Fail fast, log for alerting
- Constraint violations → Return 422 error
- RLS policy errors → Escalate (should not happen with service role)

### PromptBuilderService

**Responsibility:** Construct LLM prompts from templates

**Interface:**
```python
class PromptBuilderService:
    def build_classification_prompt(
        self,
        description: str,
        include_examples: bool = True
    ) -> str:
        """Build prompt for ticket classification"""
        ...

    def build_system_message(self) -> str:
        """Build system message for chat models"""
        ...

    def get_few_shot_examples(self, count: int = 5) -> List[Dict[str, str]]:
        """Get few-shot examples for prompt"""
        ...
```

**Implementation Strategy:**
- Template-based prompt construction
- Configurable number of few-shot examples
- Token counting to stay within limits
- Prompt versioning for A/B testing

---

## 7. DATA FLOW ARCHITECTURE

### Request Processing Flow

```
1. HTTP Request
   ↓
2. Middleware Stack
   - Request ID generation
   - Logging
   - CORS headers
   - API key validation
   ↓
3. Route Handler (/api/v1/process-ticket)
   - Request validation (Pydantic)
   - Dependency injection
   ↓
4. Business Logic (ProcessTicketUseCase)
   a. Fetch ticket from Supabase (verify exists)
   b. Check if already processed (idempotency)
   c. Mark processing started (timestamp)
   d. Call ClassifierService
      - Build prompt
      - Call LLM via LangChain
      - Parse response
      - Validate output
   e. Update Supabase with results
   f. Return response
   ↓
5. Response Serialization
   - Convert to JSON
   - Add headers
   ↓
6. HTTP Response
```

### Error Flow

```
Exception Occurs
   ↓
Exception Handler (by type)
   ↓
Log Error (structured)
   ↓
Check if retryable
   ├─ Yes → Retry with backoff
   └─ No → Convert to ErrorResponse
   ↓
Record error in database (if ticket_id known)
   ↓
Return HTTP error response (400/422/500/503)
```

### Idempotency Strategy

**Problem:** n8n may retry failed requests
**Solution:** Check `processed` flag before classification

```
IF ticket.processed == TRUE:
    RETURN existing classification (from database)
ELSE:
    PERFORM classification
    UPDATE database
    RETURN new classification
```

---

## 8. ERROR HANDLING STRATEGY

### Error Hierarchy

```python
class AppException(Exception):
    """Base application exception"""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)

class ValidationError(AppException):
    """Client-side validation error (400)"""
    pass

class NotFoundError(AppException):
    """Resource not found (404)"""
    pass

class BusinessLogicError(AppException):
    """Business rule violation (422)"""
    pass

class ExternalServiceError(AppException):
    """External service failure (502/503)"""
    pass

class LLMServiceError(ExternalServiceError):
    """LLM-specific errors"""
    pass

class DatabaseError(ExternalServiceError):
    """Database-specific errors"""
    pass
```

### Exception Handlers

**FastAPI Exception Handlers:**
```python
@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "field": getattr(exc, 'field', None)
            },
            "request_id": request.state.request_id
        }
    )

@app.exception_handler(LLMServiceError)
async def llm_error_handler(request, exc):
    # Log error with full context
    logger.error(
        "LLM service failure",
        error=exc.message,
        request_id=request.state.request_id,
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "LLM_SERVICE_ERROR",
                "message": "Failed to process ticket. Please try again.",
                "field": None
            },
            "request_id": request.state.request_id
        }
    )
```

### Retry Configuration

**Retry-Worthy Errors:**
- Network timeouts
- 429 Rate Limit (with backoff)
- 503 Service Unavailable
- Transient database connection errors

**Non-Retry Errors:**
- 400 Bad Request (client error)
- 401/403 Authentication/Authorization
- 422 Unprocessable Entity (business logic)
- 500 Internal Server Error (our bug)

**Tenacity Configuration:**
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((TimeoutError, NetworkError)),
    reraise=True
)
async def call_llm_with_retry(...):
    ...
```

---

## 9. CONFIGURATION MANAGEMENT

### Environment Variables

**Required:**
```bash
# Application
APP_ENV=production                    # Environment (dev/staging/prod)
API_PORT=8000                         # Server port
LOG_LEVEL=INFO                        # Logging level

# Security
API_KEY=your-secret-key-here          # API authentication key

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...   # Service role (NOT anon key)

# LLM Provider
LLM_PROVIDER=openai                   # openai | huggingface | anthropic
OPENAI_API_KEY=sk-...                 # If using OpenAI
HF_API_TOKEN=hf_...                   # If using HuggingFace

# LLM Configuration
LLM_MODEL=gpt-3.5-turbo               # Model name
LLM_TEMPERATURE=0.0                   # Temperature (0 = deterministic)
LLM_MAX_TOKENS=200                    # Max response tokens
LLM_TIMEOUT=10                        # Request timeout (seconds)

# Retry Configuration
MAX_RETRIES=3                         # Max retry attempts
RETRY_BACKOFF=2                       # Exponential backoff multiplier

# Feature Flags
ENABLE_METRICS=true                   # Expose /metrics endpoint
ENABLE_CONFIDENCE_SCORES=false        # Include confidence in response
```

**Optional:**
```bash
# Observability
SENTRY_DSN=https://...                # Error tracking
PROMETHEUS_PORT=9090                  # Metrics port

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60              # Max requests per minute
```

### Settings Class

**Pydantic Settings:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    # Application
    app_env: Literal["dev", "staging", "production"] = "dev"
    api_port: int = 8000
    log_level: str = "INFO"

    # Security
    api_key: str

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # LLM
    llm_provider: Literal["openai", "huggingface", "anthropic"] = "openai"
    openai_api_key: Optional[str] = None
    llm_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 200
    llm_timeout: int = 10

    # Retry
    max_retries: int = 3
    retry_backoff: int = 2

    # Features
    enable_metrics: bool = True
    enable_confidence_scores: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @validator('llm_provider')
    def validate_llm_credentials(cls, v, values):
        if v == "openai" and not values.get('openai_api_key'):
            raise ValueError("OPENAI_API_KEY required when using OpenAI")
        return v
```

---

## 10. OBSERVABILITY & MONITORING

### Structured Logging

**Log Format (JSON):**
```json
{
  "timestamp": "2026-01-22T10:30:15.123Z",
  "level": "INFO",
  "message": "Ticket processed successfully",
  "request_id": "req_abc123",
  "ticket_id": "123e4567-e89b-12d3-a456-426614174000",
  "category": "Técnico",
  "sentiment": "Negativo",
  "processing_time_ms": 1234,
  "llm_tokens": 150
}
```

**Log Levels:**
- **DEBUG:** Detailed diagnostic info (prompts, responses)
- **INFO:** Normal operations (requests, responses)
- **WARNING:** Recoverable errors (retries, fallbacks)
- **ERROR:** Unrecoverable errors (exceptions)
- **CRITICAL:** System failures (database down)

### Metrics (Prometheus)

**Request Metrics:**
```
api_requests_total{method, endpoint, status}          # Counter
api_request_duration_seconds{endpoint}                # Histogram
api_request_size_bytes{endpoint}                      # Histogram
api_response_size_bytes{endpoint}                     # Histogram
```

**Business Metrics:**
```
tickets_processed_total{category, sentiment}          # Counter
tickets_processing_failed_total{reason}               # Counter
llm_requests_total{provider, model, status}           # Counter
llm_request_duration_seconds{provider, model}         # Histogram
llm_tokens_used_total{provider, model}                # Counter
```

**System Metrics:**
```
database_connections_active                           # Gauge
database_query_duration_seconds{query_type}           # Histogram
```

### Health Checks

**Liveness Probe:** `/health/live`
- Returns 200 if server is running
- Used by orchestrator to restart unhealthy containers

**Readiness Probe:** `/health/ready`
- Returns 200 if server can handle requests
- Checks database connectivity
- Checks LLM service availability

---

## 11. SECURITY CONSIDERATIONS

### API Key Authentication

**Mechanism:**
- Header-based: `X-API-Key: your-secret-key`
- Constant-time comparison to prevent timing attacks
- Key rotation support via environment variable update

**Implementation:**
```python
async def verify_api_key(
    api_key: str = Header(..., alias="X-API-Key")
) -> None:
    expected = settings.api_key
    if not secrets.compare_digest(api_key, expected):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
```

### Input Validation

**XSS Prevention:**
- All inputs validated and sanitized
- No HTML rendering (JSON API only)
- Content-Type enforcement

**Injection Prevention:**
- Parameterized queries (Supabase client handles this)
- No dynamic SQL construction
- Input length limits enforced

**DoS Prevention:**
- Request size limits (10KB max)
- Rate limiting (60 req/min per key)
- Timeout enforcement (10s max per request)

### Secrets Management

**Development:**
- `.env` file (gitignored)
- `.env.example` template committed

**Production:**
- Environment variables via platform (Railway, Render)
- Secret rotation every 90 days
- Never log secrets (sanitize in logging middleware)

### CORS Configuration

**Allowed Origins:**
- Development: `http://localhost:3000`, `http://localhost:5173`
- Production: `https://dashboard.example.com`
- n8n webhook: `https://n8n.cloud`

**Allowed Methods:**
- `POST` (for /process-ticket)
- `GET` (for /health)

**Allowed Headers:**
- `Content-Type`
- `X-API-Key`

---

## 12. TESTING STRATEGY

### Unit Tests (70% coverage target)

**Test Scope:**
- Service layer logic (ClassifierService, SupabaseService)
- Prompt building logic
- Validation logic
- Error handling

**Mocking:**
- Mock LLM responses (no real API calls)
- Mock Supabase client (in-memory fake)
- Mock external dependencies

**Example Test Structure:**
```python
async def test_classifier_returns_valid_category():
    # Arrange
    mock_llm = MockLLM(response='{"category": "Técnico", "sentiment": "Negativo"}')
    classifier = ClassifierService(llm=mock_llm)

    # Act
    result = await classifier.classify_ticket("Mi internet no funciona")

    # Assert
    assert result.category == TicketCategory.TECNICO
    assert result.sentiment == TicketSentiment.NEGATIVO
```

### Integration Tests (20% coverage target)

**Test Scope:**
- API endpoints (full request/response cycle)
- Database interactions (using test database)
- LLM integration (using mock or test API keys)

**Test Database:**
- Separate Supabase project for testing
- Reset before each test suite run
- Seed with test data

**Example Test:**
```python
async def test_process_ticket_endpoint_success(client: TestClient):
    # Arrange
    ticket_id = create_test_ticket(description="Test ticket")

    # Act
    response = client.post(
        "/api/v1/process-ticket",
        json={"ticket_id": str(ticket_id), "description": "Test ticket"},
        headers={"X-API-Key": "test-key"}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["classification"]["category"] in ["Técnico", "Facturación", "Comercial"]
```

### E2E Tests (10% coverage target)

**Test Scope:**
- Full flow: n8n → API → Supabase → Dashboard
- Real LLM calls (with test quota)
- Real database updates

**Test Environment:**
- Staging environment with production-like setup
- Run before deployment to production

---

## 13. DEPLOYMENT ARCHITECTURE

### Container Configuration

**Dockerfile Strategy:**
- Multi-stage build (builder + runtime)
- Python 3.11 slim base image
- Non-root user for security
- Health check built-in
- Layer caching for fast rebuilds

**Resource Requirements:**
```yaml
resources:
  requests:
    memory: 256Mi
    cpu: 250m
  limits:
    memory: 512Mi
    cpu: 500m
```

### Platform: Railway.app (Recommended)

**Advantages:**
- Free tier: 500 hours/month
- Automatic HTTPS
- Environment variable management
- Auto-deploy from Git
- Built-in logging and metrics

**Configuration:**
```yaml
# railway.toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health/live"
healthcheckTimeout = 10
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### Alternative: Render.com

**Advantages:**
- Free tier: 750 hours/month
- Background workers support
- Cron jobs for maintenance
- PostgreSQL included

**Configuration:**
```yaml
# render.yaml
services:
  - type: web
    name: support-copilot-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    healthCheckPath: /health/live
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
```

### Environment-Specific Configuration

**Development:**
- Hot reload enabled
- Debug logging
- Permissive CORS
- Mock LLM for fast iteration

**Staging:**
- Production-like configuration
- Test LLM provider
- Separate Supabase project
- Monitoring enabled

**Production:**
- Optimized for performance
- Production LLM provider
- Strict CORS
- Full monitoring and alerting

---

## 14. PERFORMANCE OPTIMIZATION

### Response Time Budget

```
Total: 5000ms (p95 target)
├─ Request validation: 10ms
├─ Database fetch: 50ms
├─ Prompt building: 20ms
├─ LLM call: 4000ms (largest component)
├─ Response parsing: 100ms
├─ Database update: 200ms
└─ Response serialization: 20ms
```

### Optimization Strategies

**1. Async/Await Throughout**
- All I/O operations async (database, HTTP)
- Concurrent operations where possible
- asyncio gather for parallel tasks

**2. Connection Pooling**
- Reuse HTTP connections to LLM provider
- Reuse Supabase client connections
- Configure pool size based on load

**3. Caching Strategy**
- Cache prompt templates (in-memory)
- Cache LLM responses for duplicate tickets (Redis, optional)
- Cache Supabase schema metadata

**4. Request Batching (Future Enhancement)**
- Batch multiple tickets in single LLM call
- Reduces overhead, improves throughput
- Requires prompt engineering changes

**5. Model Optimization**
- Use faster model (GPT-3.5 vs GPT-4)
- Reduce max_tokens to minimum needed
- Consider local model deployment (Hugging Face)

---

## 15. EDGE CASES & CORNER CASES

### Scenario 1: Duplicate Request (Idempotency)
**Situation:** n8n retries after network timeout
**Handling:** Check `processed` flag, return cached result

### Scenario 2: Malformed LLM Response
**Situation:** LLM returns invalid JSON or wrong format
**Handling:** Fallback to defaults (Técnico + Neutral), log for review

### Scenario 3: Ticket Already Processed
**Situation:** Request for already-processed ticket
**Handling:** Return existing classification from database

### Scenario 4: Database Connection Lost Mid-Request
**Situation:** Supabase goes down during processing
**Handling:** Rollback to unprocessed state, return 503 error

### Scenario 5: LLM Rate Limit Hit
**Situation:** Too many requests in short time
**Handling:** Exponential backoff (1s, 2s, 4s), then fail with 503

### Scenario 6: Extremely Long Ticket Description
**Situation:** Description exceeds token limit
**Handling:** Truncate to first 1000 characters, add note

### Scenario 7: Non-Spanish Text
**Situation:** English or other language ticket
**Handling:** Process normally (model is multilingual), may have lower accuracy

### Scenario 8: Empty/Whitespace-Only Description
**Situation:** Description is "   " after cleaning
**Handling:** Return 400 validation error

---

## 16. FUTURE ENHANCEMENTS

### Phase 2 Features

**1. Confidence Scores**
- Add probability scores from LLM
- Allow manual review for low-confidence tickets

**2. Batch Processing**
- Accept array of tickets
- Process concurrently (up to 10 at once)
- Return array of results

**3. Webhook Callbacks**
- Optional callback URL in request
- POST results when processing completes
- Useful for async workflows

**4. Custom Categories**
- Support tenant-specific categories
- Dynamic prompt building based on org

**5. Multi-Language Support**
- Detect language automatically
- Use language-specific prompts
- Support English, Portuguese, etc.

**6. Analytics Endpoint**
- GET /api/v1/analytics
- Return processing stats
- Category/sentiment distribution

**7. Reprocessing Endpoint**
- POST /api/v1/reprocess-ticket
- Force reprocess already-processed ticket
- Useful for prompt iteration

---

## 17. IMPLEMENTATION CHECKLIST

### Phase 1: Core Functionality
- [ ] Project structure setup
- [ ] Configuration management (pydantic-settings)
- [ ] Pydantic models (request/response/domain)
- [ ] FastAPI app initialization
- [ ] Health check endpoints
- [ ] Supabase client service
- [ ] LangChain classifier service
- [ ] Prompt builder service
- [ ] POST /process-ticket endpoint
- [ ] Error handling middleware
- [ ] API key authentication
- [ ] Structured logging setup

### Phase 2: Quality & Testing
- [ ] Unit tests (services)
- [ ] Integration tests (API)
- [ ] Type checking (mypy)
- [ ] Linting (ruff)
- [ ] Code formatting (black, isort)
- [ ] Pre-commit hooks
- [ ] Coverage reports (>80%)

### Phase 3: Observability
- [ ] Request ID middleware
- [ ] Prometheus metrics
- [ ] Detailed error logging
- [ ] Performance monitoring
- [ ] Alerting setup

### Phase 4: Deployment
- [ ] Dockerfile creation
- [ ] docker-compose for local dev
- [ ] Environment variables documentation
- [ ] Railway/Render deployment
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Smoke tests post-deployment

### Phase 5: Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] README with setup instructions
- [ ] Environment variables guide
- [ ] Deployment guide
- [ ] Troubleshooting guide

---

## 18. DESIGN SUMMARY

### Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Web Framework** | FastAPI | Async support, automatic docs, type safety |
| **LLM Orchestration** | LangChain | Abstraction over providers, prompt management |
| **Database Client** | Supabase Python SDK | Official client, realtime support |
| **Validation** | Pydantic v2 | Type safety, automatic validation |
| **Logging** | structlog | Structured JSON logs |
| **Retry Logic** | tenacity | Declarative, configurable |
| **Deployment** | Railway.app | Free tier, easy deployment |
| **Type Checking** | mypy (strict) | Catch bugs early |

### Success Criteria

✅ **Functional:** Correctly classifies 85%+ tickets
✅ **Performance:** p95 latency < 5 seconds
✅ **Reliability:** 99% uptime, < 1% error rate
✅ **Maintainability:** 100% type coverage, 80%+ test coverage
✅ **Security:** API key auth, input validation, no secrets in logs
✅ **Observability:** Structured logs, Prometheus metrics, health checks

---

**Ready for implementation!** 🚀
