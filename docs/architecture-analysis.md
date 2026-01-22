# AI-Powered Support Co-Pilot - Architecture Analysis

**Role:** Senior Full-Stack AI Engineer Analysis
**Date:** 2026-01-22
**Project:** VIVETORI Technical Challenge

---

## 1. SYSTEM SUMMARY

**AI-Powered Support Co-Pilot** is an end-to-end intelligent ticketing system that automatically processes, categorizes, and analyzes support tickets using AI agents. The system provides real-time visualization and automated notifications for critical tickets.

### Core Capabilities
- Automatic ticket ingestion and storage
- AI-powered categorization (Technical, Billing, Commercial)
- Sentiment analysis (Positive, Neutral, Negative)
- Real-time dashboard updates
- Automated alerting for negative sentiment tickets
- Complete audit trail of processed tickets

### Technology Stack
- **Database:** Supabase (PostgreSQL + Real-time subscriptions)
- **AI Microservice:** Python + FastAPI + LangChain
- **Automation:** n8n (low-code workflow orchestration)
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS

---

## 2. GENERAL ARCHITECTURE

### Data Flow Architecture

```
[Ticket Creation] → [Supabase DB] → [n8n Trigger] → [FastAPI Service] → [LLM Processing]
                          ↓                                                      ↓
                    [Realtime Channel] ← ← ← ← ← ← ← ← ← ← [Update DB Record]
                          ↓
                   [React Dashboard]
                          ↓
                  [Conditional Branch: Negative Sentiment] → [Email Notification]
```

### Component Breakdown

#### A. Supabase Layer (Data & Real-time)
- **tickets table** with schema:
  - `id` (UUID PK)
  - `created_at` (Timestamp)
  - `description` (Text)
  - `category` (Text/Enum: Técnico, Facturación, Comercial)
  - `sentiment` (Text: Positivo, Neutral, Negativo)
  - `processed` (Boolean, default: false)
- **Row Level Security (RLS)** policies for secure access
- **Realtime channels** for live updates to frontend

#### B. FastAPI Microservice (AI Processing Engine)
- **Endpoint:** `POST /process-ticket`
- **Input:** `{ "ticket_id": "uuid", "description": "text" }`
- **Processing Pipeline:**
  1. Receive ticket text
  2. Construct prompt for LLM (LangChain orchestration)
  3. Call LLM (Hugging Face or OpenAI-compatible model)
  4. Parse structured JSON response: `{category, sentiment}`
  5. Update Supabase record: set category, sentiment, processed=true
- **Response:** `{ "success": true, "category": "...", "sentiment": "..." }`
- **Deployment:** Render.com / Railway.app (containerized)

#### C. n8n Workflow Orchestration
- **Trigger:** Supabase new row insertion OR webhook
- **Workflow Steps:**
  1. Detect new unprocessed ticket
  2. Call FastAPI `/process-ticket` endpoint
  3. Conditional logic: if sentiment == "Negativo"
  4. Send email notification (simulated or real SMTP)
  5. Optional: Log to monitoring service
- **Export:** JSON workflow file for version control

#### D. React Frontend Dashboard
- **Real-time Data Sync:**
  - Supabase client subscription to `tickets` table
  - Automatic UI updates on INSERT/UPDATE events
- **UI Components:**
  - Ticket list with category badges
  - Sentiment indicators (color-coded)
  - Filter/search capabilities
  - Processing status visibility
- **Styling:** Tailwind CSS utility-first approach
- **Deployment:** Vercel / Netlify (static hosting)

---

## 3. TECHNICAL RISKS

### High Priority Risks

#### R1: LLM API Rate Limiting / Quota Exhaustion
- **Impact:** Processing pipeline breaks when limit exceeded
- **Mitigation:**
  - Implement exponential backoff retry logic
  - Queue system for ticket processing (Redis/Bull)
  - Use local models (Hugging Face Transformers) for free tier
  - Circuit breaker pattern to prevent cascade failures

#### R2: Real-time Connection Stability
- **Impact:** Dashboard doesn't reflect current state
- **Mitigation:**
  - Implement reconnection logic in Supabase client
  - Fallback to polling mechanism (every 5s)
  - Visual indicator for connection status
  - Local state caching with optimistic updates

#### R3: n8n Workflow Execution Failures
- **Impact:** Tickets remain unprocessed
- **Mitigation:**
  - Error handling nodes in n8n workflow
  - Dead letter queue for failed processing
  - Manual retry mechanism in dashboard
  - Monitoring alerts for workflow errors

#### R4: Supabase Free Tier Limitations
- **Impact:** Database size (500MB), API requests (50K/month), realtime connections (200 concurrent)
- **Mitigation:**
  - Implement data retention policies (archive old tickets)
  - Pagination and lazy loading on frontend
  - Connection pooling and cleanup
  - Upgrade plan if needed during demo

### Medium Priority Risks

#### R5: Prompt Engineering Inconsistency
- **Impact:** Incorrect categorization or sentiment analysis
- **Mitigation:**
  - Few-shot learning examples in prompt
  - Output validation schema (JSON Schema / Pydantic)
  - Confidence scores for predictions
  - Human-in-the-loop for low confidence cases

#### R6: Cold Start Latency (Serverless)
- **Impact:** First request takes 10-30s on Render free tier
- **Mitigation:**
  - Keep-alive ping service (cron job)
  - Loading states in UI
  - Async processing with status updates
  - Consider always-on deployment tier

#### R7: CORS and Authentication Issues
- **Impact:** Frontend can't access APIs
- **Mitigation:**
  - Proper CORS configuration in FastAPI
  - Supabase anon key with RLS policies
  - API key authentication for n8n→FastAPI
  - Environment variable management

### Low Priority Risks

#### R8: Data Consistency During Concurrent Updates
- **Impact:** Race conditions on ticket updates
- **Mitigation:**
  - Optimistic locking with version column
  - Database transactions in update operations
  - Idempotency keys for API requests

---

## 4. KEY TECHNICAL DECISIONS

### Decision 1: LLM Provider Selection

**Options Evaluated:**
- **OpenAI GPT-3.5/4** (via LangChain)
  - Pros: High accuracy, structured output support, easy integration
  - Cons: Requires API key, costs per token, external dependency
- **Hugging Face Models** (distilbert, BERT-based)
  - Pros: Free, self-hosted, no rate limits
  - Cons: Lower accuracy, requires GPU for speed, model management
- **Anthropic Claude** (via LangChain)
  - Pros: Strong instruction following, good for classification
  - Cons: API costs, similar limitations to OpenAI

**Recommendation:** **Start with Hugging Face (free tier), provide OpenAI as optional upgrade**
- Use `facebook/bart-large-mnli` for zero-shot classification
- Use `distilbert-base-uncased-finetuned-sst-2-english` for sentiment
- Implement adapter pattern to easily swap providers

---

### Decision 2: n8n Trigger Strategy

**Options:**
- **Supabase Trigger (Database Webhooks)**
  - Pros: Direct integration, automatic on INSERT
  - Cons: Requires webhook endpoint configuration
- **Polling (Every X seconds)**
  - Pros: Simple setup, no webhook needed
  - Cons: Inefficient, delay in processing
- **Manual Webhook (Frontend→n8n→FastAPI)**
  - Pros: Full control, immediate processing
  - Cons: Tight coupling between components

**Recommendation:** **Hybrid Approach - Supabase Database Webhook + Manual Fallback**
- Configure Supabase webhook to trigger n8n on new rows
- Add manual "Reprocess" button in frontend calling n8n webhook
- Best of both worlds: automatic + manual control

---

### Decision 3: Frontend State Management

**Options:**
- **React Context + useReducer**
  - Pros: Built-in, no dependencies, simple for small apps
  - Cons: Re-render issues, verbose for complex state
- **Zustand / Jotai**
  - Pros: Lightweight, modern, TypeScript-friendly
  - Cons: Additional dependency, team learning curve
- **TanStack Query (React Query)**
  - Pros: Excellent for server state, caching, real-time sync
  - Cons: Overkill for simple CRUD

**Recommendation:** **Supabase Real-time + React Context (minimal approach)**
- Supabase client handles data fetching + real-time subscriptions
- Minimal local state for UI concerns (filters, modals)
- No additional state library needed for this scope

---

### Decision 4: Deployment Strategy

**Components Mapping:**

| Component | Platform | Rationale |
|-----------|----------|-----------|
| **FastAPI** | Railway.app | Free tier, Docker support, persistent logs, easy env vars |
| **Frontend** | Vercel | Zero-config deployment, instant CDN, preview URLs |
| **n8n** | Self-hosted (n8n Cloud) | Cloud version has free tier, webhook-ready, export/import workflows |
| **Supabase** | Supabase Cloud | Managed service, free tier sufficient, built-in realtime |

**CI/CD:** GitHub Actions for automated deployment on push to main branch

---

### Decision 5: Prompt Engineering Strategy

**Chosen Approach: Structured Output with Few-Shot Examples**

```python
prompt_template = """
You are a support ticket classifier. Analyze the following ticket and return ONLY a JSON object.

Examples:
Input: "My bill is incorrect, charged twice this month"
Output: {"category": "Facturación", "sentiment": "Negativo"}

Input: "How do I reset my password?"
Output: {"category": "Técnico", "sentiment": "Neutral"}

Input: "Your product is amazing! Just wanted to say thanks"
Output: {"category": "Comercial", "sentiment": "Positivo"}

Now classify this ticket:
Input: {ticket_description}
Output:
"""
```

**Validation Layer:**
- Pydantic model for output parsing
- Fallback to "Técnico" if category unclear
- Fallback to "Neutral" if sentiment unclear
- Log confidence scores for future fine-tuning

---

## 5. DETAILED REQUIREMENTS

### Functional Requirements (FR)

**FR1: Ticket Storage**
- System shall store tickets in Supabase with all required fields
- Each ticket shall have unique UUID identifier
- Timestamp shall be automatically generated on creation

**FR2: AI-Powered Classification**
- System shall categorize tickets into: Técnico, Facturación, Comercial
- System shall analyze sentiment as: Positivo, Neutral, Negativo
- Classification shall be performed via LangChain + LLM

**FR3: Processing Status Tracking**
- System shall mark tickets as processed after AI analysis
- Unprocessed tickets shall be identifiable

**FR4: Automated Workflow**
- n8n shall automatically trigger on new ticket creation
- Workflow shall call FastAPI endpoint with ticket data
- Negative sentiment tickets shall trigger email notifications

**FR5: Real-time Dashboard**
- Frontend shall display all tickets in real-time
- Updates shall appear without manual refresh
- UI shall show category and sentiment for each ticket

**FR6: API Endpoint**
- FastAPI shall expose POST /process-ticket endpoint
- Endpoint shall accept ticket ID and description
- Response shall include extracted category and sentiment

### Non-Functional Requirements (NFR)

**NFR1: Performance**
- Ticket processing shall complete within 10 seconds (95th percentile)
- Dashboard shall load initial data within 2 seconds
- Real-time updates shall propagate within 1 second

**NFR2: Scalability**
- System shall handle 100 concurrent users (within free tier limits)
- Database shall support 10,000 tickets minimum
- API shall support 50 requests per minute

**NFR3: Reliability**
- System uptime shall be 99% (excluding platform maintenance)
- Failed processing attempts shall be logged and retryable
- Data consistency shall be maintained across all components

**NFR4: Security**
- Database access shall be protected by RLS policies
- API keys shall be stored as environment variables
- Frontend shall use Supabase anon key (not service role)

**NFR5: Maintainability**
- Code shall use TypeScript for type safety
- API shall include error handling and logging
- Components shall be modular and testable

**NFR6: Usability**
- Dashboard shall be responsive (mobile-friendly)
- Loading states shall indicate processing
- Error messages shall be user-friendly

**NFR7: Deployability**
- Services shall be deployable to free-tier platforms
- Deployment shall be automated via CI/CD
- Configuration shall use environment variables

---

## 6. COMPONENT DEPENDENCIES

### Dependencies Matrix

| Component | Depends On | Dependency Type | Critical Path |
|-----------|-----------|-----------------|---------------|
| **Frontend** | Supabase | Data + Realtime | Yes |
| **Frontend** | FastAPI | Optional (manual reprocess) | No |
| **n8n** | Supabase | Trigger source | Yes |
| **n8n** | FastAPI | Processing service | Yes |
| **FastAPI** | Supabase | Database updates | Yes |
| **FastAPI** | LLM Provider | AI processing | Yes |
| **n8n** | Email Service | Notifications | No |

**Critical Path:** Supabase → n8n → FastAPI → LLM → Supabase → Frontend

---

## 7. IMPLEMENTATION PHASES

### Phase 1: Foundation (Day 1)
1. Set up Supabase project and create tickets table
2. Configure RLS policies for secure access
3. Create FastAPI project structure with basic health endpoint
4. Set up frontend scaffolding with Vite + React + TypeScript

### Phase 2: Core Processing (Day 2)
1. Implement `/process-ticket` endpoint with LangChain integration
2. Add Pydantic models for validation
3. Connect FastAPI to Supabase for updates
4. Test classification with sample tickets

### Phase 3: Automation (Day 3)
1. Create n8n workflow with Supabase trigger
2. Add FastAPI call node
3. Implement conditional email notification
4. Test end-to-end flow

### Phase 4: Frontend (Day 4)
1. Implement Supabase client connection
2. Build ticket list UI with Tailwind
3. Add real-time subscription
4. Style with sentiment indicators

### Phase 5: Deployment & Polish (Day 5)
1. Deploy FastAPI to Railway
2. Deploy frontend to Vercel
3. Configure environment variables
4. Test production environment
5. Document README with URLs and explanations

---

## 8. MONITORING & OBSERVABILITY

### Metrics to Track
- Ticket processing success rate
- Average processing time
- LLM API response times
- Real-time connection stability
- Classification accuracy (manual validation sample)

### Recommended Tools
- **Logging:** Python `logging` module + Railway logs
- **Error Tracking:** Sentry (free tier) for FastAPI
- **Uptime Monitoring:** UptimeRobot for API health checks
- **Analytics:** Simple counter in Supabase for processed tickets

---

## 9. CONCLUSION

This architecture provides a **production-ready foundation** that demonstrates:
- Full-stack capabilities (database, backend, automation, frontend)
- AI/ML integration with practical prompt engineering
- Modern DevOps practices (containerization, CI/CD, cloud deployment)
- Real-time systems architecture
- Low-code tool integration (n8n)

The system is designed to be **scalable beyond the demo** by:
- Using industry-standard frameworks (FastAPI, React)
- Implementing proper error handling and retry logic
- Maintaining separation of concerns
- Supporting multiple LLM providers through abstraction

**Estimated Total Development Time:** 3-5 days for a senior engineer with all components deployed and functional.

---

## 10. DELIVERABLES CHECKLIST

- [ ] `/supabase/setup.sql` - Database schema and RLS policies
- [ ] `/python-api/` - FastAPI service with requirements.txt and Dockerfile
- [ ] `/n8n-workflow/workflow.json` - n8n workflow export
- [ ] `/frontend/` - React dashboard source code
- [ ] `README.md` with:
  - [ ] Live dashboard URL
  - [ ] Live API URL
  - [ ] Prompt engineering strategy explanation
- [ ] GitHub repository with proper structure
- [ ] All services deployed and functional
