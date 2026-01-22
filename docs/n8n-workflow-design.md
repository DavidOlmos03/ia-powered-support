# n8n Workflow Design - AI-Powered Support Co-Pilot

**Role:** Senior Automation Engineer (n8n Expert)
**Date:** 2026-01-22
**Workflow:** Automatic ticket processing with sentiment-based alerting
**Integration:** Supabase → FastAPI → Email Notification

---

## 1. WORKFLOW OVERVIEW

### Purpose
Automatically process new support tickets by:
1. Detecting unprocessed tickets in Supabase
2. Calling FastAPI microservice for AI classification
3. Evaluating sentiment
4. Sending email alerts for negative sentiment tickets

### Trigger Mechanism
**Polling-based** (Supabase has no native real-time trigger in n8n)
- Poll every 60 seconds for new unprocessed tickets
- Filter by `processed = false`
- Order by `created_at DESC` to get newest first

### Data Flow
```
[Supabase Trigger] → [HTTP Request to FastAPI] → [IF: Sentiment Check]
                                                         ↓
                                                   [Negativo?]
                                                    ↙        ↘
                                               [Yes]        [No]
                                                 ↓            ↓
                                          [Send Email]   [Do Nothing]
                                                 ↓            ↓
                                            [End]        [End]
```

---

## 2. NODE ARCHITECTURE

### Node 1: Schedule Trigger
**Type:** `Schedule Trigger`
**Purpose:** Initiate workflow execution periodically

**Configuration:**
- **Trigger Interval:** Every 1 minute (60 seconds)
- **Trigger Times:** All day (00:00 - 23:59)
- **Run on Start:** No (prevents immediate execution on deployment)

**Why This Node:**
- n8n doesn't have native Supabase real-time trigger
- Polling is reliable and simple for MVP
- 60-second interval balances responsiveness vs API load

**Output:**
```json
{
  "timestamp": "2026-01-22T10:30:00Z"
}
```

---

### Node 2: Supabase - Get Unprocessed Tickets
**Type:** `HTTP Request` (to Supabase REST API)
**Purpose:** Fetch tickets that haven't been processed yet

**Configuration:**
- **Method:** GET
- **URL:** `{{$env.SUPABASE_URL}}/rest/v1/tickets`
- **Authentication:** API Key (Header)
  - Header: `apikey`
  - Value: `{{$env.SUPABASE_ANON_KEY}}`
  - Header: `Authorization`
  - Value: `Bearer {{$env.SUPABASE_ANON_KEY}}`
- **Query Parameters:**
  - `processed=eq.false` - Only unprocessed tickets
  - `order=created_at.desc` - Newest first
  - `limit=10` - Process max 10 at a time (prevent overwhelming API)
  - `select=id,description,created_at` - Only needed fields

**Headers:**
```
Content-Type: application/json
apikey: {{$env.SUPABASE_ANON_KEY}}
Authorization: Bearer {{$env.SUPABASE_ANON_KEY}}
Prefer: return=representation
```

**Response Handling:**
- **Success (200):** Array of ticket objects
- **Empty Array:** No tickets to process (workflow ends)
- **Error (4xx/5xx):** Retry or log error

**Output Example:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "description": "Mi conexión a internet no funciona",
    "created_at": "2026-01-22T10:25:00Z"
  }
]
```

**Important Notes:**
- Use `anon` key (not service role) for read operations
- RLS policies must allow read access
- Response is an array (even if empty)

---

### Node 3: Split Into Items
**Type:** `Split In Batches` or `Item Lists`
**Purpose:** Convert array of tickets into individual items for processing

**Configuration:**
- **Batch Size:** 1 (process one ticket at a time)
- **Options:** Reset (re-execute for each item)

**Why This Node:**
- Supabase returns an array, but we need to process each ticket individually
- Allows parallel processing in future (change batch size)
- Each subsequent node runs once per ticket

**Data Transformation:**
```
Input:  [ticket1, ticket2, ticket3]
Output: ticket1 (first iteration)
        ticket2 (second iteration)
        ticket3 (third iteration)
```

**Alternative Approach:**
Use `Loop Over Items` node if splitting is not needed

---

### Node 4: HTTP Request - Call FastAPI
**Type:** `HTTP Request`
**Purpose:** Call FastAPI microservice to classify ticket

**Configuration:**
- **Method:** POST
- **URL:** `{{$env.FASTAPI_URL}}/api/v1/process-ticket`
- **Authentication:** Generic Credential Type
  - **Header Auth:**
    - Name: `X-API-Key`
    - Value: `{{$env.FASTAPI_API_KEY}}`
- **Body (JSON):**
```json
{
  "ticket_id": "{{$json.id}}",
  "description": "{{$json.description}}"
}
```

**Headers:**
```
Content-Type: application/json
X-API-Key: {{$env.FASTAPI_API_KEY}}
```

**Timeout:**
- Set to 15 seconds (account for LLM processing time)

**Retry Strategy:**
- **Max Attempts:** 3
- **Retry on:** 5xx errors, timeouts
- **Wait Between Retries:** Exponential (1s, 2s, 4s)
- **Do Not Retry on:** 4xx errors (client errors)

**Response Handling:**
- **Success (200):**
```json
{
  "success": true,
  "ticket_id": "123e4567-e89b-12d3-a456-426614174000",
  "classification": {
    "category": "Técnico",
    "sentiment": "Negativo"
  },
  "processing_time_ms": 1234,
  "message": "Ticket processed successfully"
}
```

- **Error (4xx/5xx):**
```json
{
  "success": false,
  "error": {
    "code": "LLM_SERVICE_ERROR",
    "message": "Failed to classify ticket"
  },
  "request_id": "req_abc123"
}
```

**Error Handling:**
- On 404 (ticket not found): Log warning, continue to next ticket
- On 500 (server error): Retry 3 times, then log error
- On 503 (service unavailable): Wait 5s, retry

---

### Node 5: IF - Check Sentiment
**Type:** `IF` (Conditional Logic)
**Purpose:** Branch workflow based on sentiment value

**Configuration:**
- **Condition Type:** String
- **Value 1:** `{{$json.classification.sentiment}}`
- **Operation:** Equal to
- **Value 2:** `Negativo`

**Logic:**
```
IF classification.sentiment == "Negativo"
  THEN → True branch (send notification)
  ELSE → False branch (do nothing)
```

**Alternative Multi-Condition:**
Could extend to:
- `Negativo` → Send urgent email
- `Neutral` → Log to monitoring
- `Positivo` → Send thank you (optional)

**Output Routing:**
- **True Output:** Tickets with negative sentiment
- **False Output:** Tickets with neutral/positive sentiment

---

### Node 6A: Send Email Notification (True Branch)
**Type:** `Send Email` or `Gmail` or `SMTP`
**Purpose:** Alert support team about negative sentiment ticket

**Configuration - Gmail:**
- **To:** `{{$env.SUPPORT_EMAIL}}` (e.g., support@company.com)
- **Subject:** `🚨 Negative Sentiment Ticket - ID: {{$json.ticket_id}}`
- **Email Type:** HTML
- **Message (HTML):**
```html
<h2>⚠️ Negative Sentiment Alert</h2>

<p>A ticket with negative sentiment has been detected and requires immediate attention.</p>

<table style="border-collapse: collapse; width: 100%;">
  <tr>
    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Ticket ID:</strong></td>
    <td style="padding: 8px; border: 1px solid #ddd;">{{$json.ticket_id}}</td>
  </tr>
  <tr>
    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Category:</strong></td>
    <td style="padding: 8px; border: 1px solid #ddd;">{{$json.classification.category}}</td>
  </tr>
  <tr>
    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Sentiment:</strong></td>
    <td style="padding: 8px; border: 1px solid #ddd;">{{$json.classification.sentiment}}</td>
  </tr>
  <tr>
    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Description:</strong></td>
    <td style="padding: 8px; border: 1px solid #ddd;">{{$json.description}}</td>
  </tr>
  <tr>
    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Created At:</strong></td>
    <td style="padding: 8px; border: 1px solid #ddd;">{{$json.created_at}}</td>
  </tr>
</table>

<p style="margin-top: 20px;">
  <a href="{{$env.DASHBOARD_URL}}/tickets/{{$json.ticket_id}}"
     style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
    View Ticket in Dashboard
  </a>
</p>

<hr>
<p style="color: #666; font-size: 12px;">
  This is an automated notification from AI-Powered Support Co-Pilot.
</p>
```

**Alternative - Slack Notification:**
- **Type:** `Slack`
- **Channel:** `#support-alerts`
- **Message:**
```
🚨 *Negative Sentiment Alert*

*Ticket ID:* {{$json.ticket_id}}
*Category:* {{$json.classification.category}}
*Sentiment:* {{$json.classification.sentiment}}
*Description:* {{$json.description}}

<{{$env.DASHBOARD_URL}}/tickets/{{$json.ticket_id}}|View in Dashboard>
```

**Alternative - Webhook:**
- **Type:** `Webhook`
- **URL:** Internal alerting system
- **Method:** POST
- **Body:**
```json
{
  "alert_type": "negative_sentiment",
  "ticket_id": "{{$json.ticket_id}}",
  "category": "{{$json.classification.category}}",
  "sentiment": "{{$json.classification.sentiment}}",
  "description": "{{$json.description}}",
  "timestamp": "{{$now}}"
}
```

---

### Node 6B: NoOp / Merge (False Branch)
**Type:** `NoOp` or `Merge`
**Purpose:** Handle non-negative sentiment tickets

**Configuration:**
- **Mode:** Pass through (do nothing)
- **Alternative:** Log to database for analytics

**Optional Actions:**
- Log to monitoring system
- Update metrics counter
- Send to data warehouse

---

### Node 7: Set Success Flag (Optional)
**Type:** `Set`
**Purpose:** Add workflow metadata for logging/monitoring

**Configuration:**
```json
{
  "workflow_status": "completed",
  "processed_at": "{{$now}}",
  "notification_sent": "{{$ifEmpty($json.email_sent, false)}}",
  "ticket_id": "{{$json.ticket_id}}"
}
```

**Why This Node:**
- Track workflow execution success
- Useful for debugging
- Can be logged to external monitoring

---

### Node 8: Error Handler (Global)
**Type:** `Error Trigger`
**Purpose:** Catch and handle any workflow errors

**Configuration:**
- **Trigger On:** Any error in workflow
- **Continue On Fail:** Yes (for all nodes except trigger)

**Error Actions:**
1. **Log Error to Database:**
   - Insert into `workflow_errors` table
   - Include: ticket_id, error_message, timestamp, node_name

2. **Send Error Notification:**
   - Email to dev team
   - Slack to #dev-alerts
   - Include full error context

3. **Retry Logic:**
   - If transient error (network, timeout): Retry
   - If permanent error (validation): Skip and log

**Error Data Structure:**
```json
{
  "error_type": "{{$json.error.name}}",
  "error_message": "{{$json.error.message}}",
  "node_name": "{{$json.node.name}}",
  "ticket_id": "{{$json.ticket_id}}",
  "timestamp": "{{$now}}",
  "stack_trace": "{{$json.error.stack}}"
}
```

---

## 3. DATA FLOW & TRANSFORMATIONS

### Flow 1: Trigger → Supabase Fetch

**Input (Trigger):**
```json
{
  "timestamp": "2026-01-22T10:30:00Z"
}
```

**Output (Supabase):**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "description": "Mi conexión a internet no funciona desde hace 3 días",
    "created_at": "2026-01-22T10:25:00Z"
  },
  {
    "id": "987fcdeb-51a2-43d7-b123-456789abcdef",
    "description": "Me cobraron dos veces este mes",
    "created_at": "2026-01-22T10:20:00Z"
  }
]
```

---

### Flow 2: Supabase → Split → FastAPI

**Input (Single Ticket after Split):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "description": "Mi conexión a internet no funciona desde hace 3 días",
  "created_at": "2026-01-22T10:25:00Z"
}
```

**FastAPI Request Body:**
```json
{
  "ticket_id": "{{$json.id}}",
  "description": "{{$json.description}}"
}
```

**FastAPI Response:**
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

---

### Flow 3: FastAPI → IF Node → Email

**Input (IF Node):**
```json
{
  "success": true,
  "ticket_id": "123e4567-e89b-12d3-a456-426614174000",
  "classification": {
    "category": "Técnico",
    "sentiment": "Negativo"
  },
  "description": "Mi conexión a internet no funciona desde hace 3 días",
  "created_at": "2026-01-22T10:25:00Z"
}
```

**IF Evaluation:**
```
{{$json.classification.sentiment}} == "Negativo"
Result: TRUE → Go to email node
```

**Email Node Variables:**
```
Subject: 🚨 Negative Sentiment Ticket - ID: 123e4567-e89b-12d3-a456-426614174000
Body: (Uses HTML template with mapped variables)
```

---

## 4. ENVIRONMENT VARIABLES

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase anon/public key | `eyJhbGciOi...` |
| `FASTAPI_URL` | FastAPI base URL | `https://api.railway.app` |
| `FASTAPI_API_KEY` | FastAPI authentication key | `secret-key-123` |
| `SUPPORT_EMAIL` | Alert recipient email | `support@company.com` |
| `DASHBOARD_URL` | Frontend dashboard URL | `https://dashboard.vercel.app` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POLLING_INTERVAL_SEC` | Trigger interval | `60` |
| `MAX_TICKETS_PER_RUN` | Batch size limit | `10` |
| `FASTAPI_TIMEOUT_SEC` | HTTP timeout | `15` |
| `RETRY_ATTEMPTS` | Max retry count | `3` |
| `SLACK_WEBHOOK_URL` | Slack notifications | - |

---

## 5. ERROR HANDLING STRATEGY

### Node-Level Error Handling

**Node 2 (Supabase Fetch):**
- **Error Type:** Network timeout
- **Action:** Retry 3 times with 5s delay
- **Final Failure:** Log error, continue workflow (skip this cycle)

**Node 4 (FastAPI Call):**
- **Error Type:** 500 Internal Server Error
- **Action:** Retry 3 times with exponential backoff
- **Final Failure:** Mark ticket with error, send alert to dev team

**Node 6A (Email Notification):**
- **Error Type:** SMTP connection failed
- **Action:** Retry 2 times
- **Final Failure:** Log error, continue (ticket was still processed)

### Workflow-Level Error Handling

**Global Error Trigger:**
```
ON ERROR:
  1. Capture error context (node, message, data)
  2. Log to error tracking system (Sentry)
  3. Send notification to dev team
  4. Update ticket with processing_error if ticket_id available
  5. Continue workflow (don't block other tickets)
```

### Circuit Breaker Pattern

**Implementation:**
- If 5 consecutive FastAPI calls fail → Pause workflow for 5 minutes
- Send alert: "FastAPI service appears to be down"
- Resume automatically after cooldown

---

## 6. OPTIMIZATION STRATEGIES

### Performance

**Batch Processing:**
- Current: Process 1 ticket at a time
- Optimization: Process up to 10 tickets in parallel
- Implementation: Change `Split In Batches` batch size to 10

**Polling Efficiency:**
- Current: Poll every 60 seconds
- Optimization: Use exponential backoff (60s → 120s → 300s) if no tickets found
- Reset to 60s when tickets are found

**Caching:**
- Cache FastAPI responses for duplicate tickets (based on description hash)
- TTL: 1 hour
- Reduces LLM API costs

### Cost Reduction

**Smart Polling:**
- Only poll during business hours (9 AM - 6 PM)
- Reduce frequency during low-traffic periods (nights/weekends)

**Batch Notifications:**
- Instead of 1 email per ticket, batch negative tickets every 15 minutes
- Send summary email with ticket count

---

## 7. MONITORING & METRICS

### Key Metrics to Track

1. **Workflow Execution Metrics:**
   - Executions per hour
   - Success rate (%)
   - Average execution time

2. **Ticket Processing Metrics:**
   - Tickets processed per day
   - Processing time (p50, p95, p99)
   - Error rate by node

3. **Classification Metrics:**
   - Category distribution (Técnico, Facturación, Comercial)
   - Sentiment distribution (Positivo, Neutral, Negativo)
   - Negative sentiment alert count

4. **Integration Health:**
   - Supabase API response time
   - FastAPI response time
   - Email delivery success rate

### Implementation

**Option 1: n8n Built-in Metrics**
- View in n8n execution history
- Limited retention (30 days)

**Option 2: External Monitoring**
- Add node to send metrics to monitoring service
- Examples: Datadog, Grafana, Custom API

**Option 3: Supabase Analytics Table**
- Create `workflow_executions` table
- Insert execution data after each run
- Query for dashboards

---

## 8. TESTING STRATEGY

### Unit Testing (Per Node)

**Test 1: Supabase Fetch**
- Scenario: No unprocessed tickets
- Expected: Empty array, workflow ends gracefully

**Test 2: FastAPI Call**
- Scenario: Valid ticket
- Expected: 200 OK with classification

**Test 3: IF Node**
- Scenario: Sentiment = "Negativo"
- Expected: Route to email node

**Test 4: Email Node**
- Scenario: Send notification
- Expected: Email delivered successfully

### Integration Testing (End-to-End)

**Test Scenario 1: Happy Path**
1. Insert test ticket with negative description
2. Wait for workflow to execute
3. Verify: Email received
4. Verify: Ticket marked as processed in Supabase

**Test Scenario 2: Positive Sentiment**
1. Insert test ticket with positive description
2. Wait for workflow to execute
3. Verify: No email sent
4. Verify: Ticket marked as processed

**Test Scenario 3: FastAPI Error**
1. Stop FastAPI service
2. Insert test ticket
3. Verify: Error logged
4. Verify: Retry attempts made
5. Verify: Dev alert sent

### Test Data

**Negative Sentiment Ticket:**
```json
{
  "description": "Estoy muy frustrado, el servicio no funciona hace 3 días y nadie me ayuda"
}
```

**Positive Sentiment Ticket:**
```json
{
  "description": "Excelente servicio, muchas gracias por la rápida respuesta"
}
```

**Neutral Sentiment Ticket:**
```json
{
  "description": "¿Cómo puedo cambiar mi contraseña?"
}
```

---

## 9. DEPLOYMENT CHECKLIST

### Pre-Deployment

- [ ] All environment variables configured in n8n
- [ ] Supabase connection tested
- [ ] FastAPI endpoint accessible
- [ ] Email/SMTP credentials configured
- [ ] Test tickets created in database

### Deployment Steps

1. **Import workflow to n8n**
2. **Set environment variables**
3. **Test with manual execution** (Execute Workflow button)
4. **Verify Supabase fetch works**
5. **Verify FastAPI call succeeds**
6. **Test email delivery**
7. **Activate workflow** (enable trigger)
8. **Monitor first 10 executions**

### Post-Deployment

- [ ] Monitor execution logs for 24 hours
- [ ] Verify email notifications are sent
- [ ] Check error rate < 1%
- [ ] Confirm tickets are marked as processed
- [ ] Review processing times (target < 10s per ticket)

---

## 10. FUTURE ENHANCEMENTS

### Phase 2 Features

**1. Advanced Routing:**
- Route by category:
  - Técnico → Engineering team
  - Facturación → Finance team
  - Comercial → Sales team

**2. Priority Scoring:**
- Calculate urgency based on:
  - Sentiment (Negativo = high priority)
  - Keywords (e.g., "urgente", "inmediato")
  - Customer tier (VIP customers get higher priority)

**3. Multi-Channel Notifications:**
- Email for all negative tickets
- SMS for critical tickets
- Slack for real-time alerts
- Push notifications to mobile app

**4. Automatic Response:**
- For positive tickets: Send thank you email
- For neutral questions: Auto-reply with FAQ link
- For negative tickets: Acknowledge issue, provide ticket number

**5. Escalation Logic:**
- If ticket not responded to in 1 hour → Escalate to manager
- If 3+ negative tickets from same customer → Flag account

**6. Analytics Dashboard:**
- Real-time metrics on workflow execution
- Sentiment trends over time
- Category distribution charts
- Response time tracking

**7. A/B Testing:**
- Test different notification templates
- Measure response times
- Optimize for engagement

---

## 11. TROUBLESHOOTING GUIDE

### Issue 1: Workflow Not Triggering

**Symptoms:** No executions in history

**Diagnosis:**
- Check if workflow is activated (toggle in top-right)
- Verify trigger schedule is configured
- Check n8n service is running

**Solution:**
- Re-activate workflow
- Test with manual execution first

---

### Issue 2: No Tickets Found

**Symptoms:** Supabase returns empty array

**Diagnosis:**
- Verify tickets exist with `processed = false`
- Check RLS policies allow read access
- Test Supabase URL and API key

**Solution:**
- Insert test ticket manually
- Verify query parameters in Supabase node
- Check anon key has correct permissions

---

### Issue 3: FastAPI Timeout

**Symptoms:** HTTP Request node times out

**Diagnosis:**
- Check FastAPI service is running
- Verify URL is correct
- Check API key is valid
- Test FastAPI directly with curl

**Solution:**
- Increase timeout to 20s
- Check FastAPI logs for errors
- Verify LLM provider (OpenAI) is accessible

---

### Issue 4: Email Not Sent

**Symptoms:** No email received despite negative sentiment

**Diagnosis:**
- Check IF node condition is correct
- Verify email credentials
- Check spam folder
- Review email node execution logs

**Solution:**
- Test email node independently
- Verify SMTP settings
- Check email address is valid

---

### Issue 5: Duplicate Processing

**Symptoms:** Same ticket processed multiple times

**Diagnosis:**
- Ticket not marked as processed in database
- FastAPI idempotency not working
- Multiple workflow instances running

**Solution:**
- Verify FastAPI updates `processed = true`
- Check only one workflow instance is active
- Add deduplication logic (check last processed timestamp)

---

## 12. WORKFLOW DIAGRAM (ASCII)

```
┌─────────────────────┐
│  Schedule Trigger   │
│  (Every 60 seconds) │
└──────────┬──────────┘
           │
           v
┌─────────────────────────────┐
│  HTTP Request: Supabase     │
│  GET /tickets               │
│  ?processed=eq.false        │
│  &limit=10                  │
└──────────┬──────────────────┘
           │
           │ (Array of tickets)
           v
┌─────────────────────────────┐
│  Split Into Items           │
│  (Loop over each ticket)    │
└──────────┬──────────────────┘
           │
           │ (Individual ticket)
           v
┌─────────────────────────────┐
│  HTTP Request: FastAPI      │
│  POST /process-ticket       │
│  Body: {ticket_id, desc}    │
└──────────┬──────────────────┘
           │
           │ (Classification result)
           v
┌─────────────────────────────┐
│  IF Node: Check Sentiment   │
│  condition.sentiment ==     │
│  "Negativo"                 │
└──────┬──────────────┬───────┘
       │              │
   [TRUE]          [FALSE]
       │              │
       v              v
┌─────────────┐  ┌──────────┐
│ Send Email  │  │  NoOp    │
│ Notification│  │ (Skip)   │
└─────────────┘  └──────────┘
       │              │
       └──────┬───────┘
              v
         ┌─────────┐
         │   END   │
         └─────────┘
```

---

## 13. DESIGN SUMMARY

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Trigger Type** | Schedule (Polling) | Supabase has no native n8n trigger |
| **Polling Interval** | 60 seconds | Balances responsiveness vs load |
| **Batch Size** | 10 tickets max | Prevents API overload |
| **Error Strategy** | Retry with backoff | Handles transient failures |
| **Notification** | Email (with alternatives) | Simple, reliable, widely supported |
| **Data Mapping** | Direct JSON mapping | Clean, maintainable |

### Success Criteria

✅ **Functional:** Processes 100% of new tickets within 2 minutes
✅ **Reliable:** <1% error rate on successful executions
✅ **Performant:** <10 seconds per ticket (including FastAPI call)
✅ **Observable:** Logs all executions and errors
✅ **Maintainable:** Clear node names, documented logic
✅ **Scalable:** Can handle 100+ tickets/day without changes

### Node Count
- **Total Nodes:** 7-8 (depending on error handling complexity)
- **Critical Path:** 5 nodes (Trigger → Supabase → Split → FastAPI → IF → Email)
- **Complexity:** Low-to-Medium (suitable for production MVP)

---

**Ready for JSON implementation!** 🚀
