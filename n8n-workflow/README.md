# n8n Workflow - AI Support Co-Pilot

This directory contains the n8n workflow for automated ticket processing with AI classification and sentiment-based alerting.

## Files

- `workflow.json` - Main workflow (Schedule Trigger + Supabase Polling)
- `workflow-webhook.json` - Alternative workflow (Webhook Trigger)

## Workflow Overview

### Main Workflow (workflow.json)

**Trigger:** Schedule (every 1 minute)

**Flow:**
```
Schedule → Get Unprocessed Tickets (Supabase) → Split Items →
Call FastAPI → Check Sentiment →
    ├─ Negative: Simulate Email
    └─ Other: Log
```

**Nodes:**
1. **Schedule Trigger** - Runs every 60 seconds
2. **Get Unprocessed Tickets** - HTTP GET to Supabase REST API
3. **Check If Tickets Exist** - Validates response has data
4. **Split Into Items** - Loops over each ticket
5. **Call FastAPI Classifier** - POST to `/api/v1/process-ticket`
6. **Is Sentiment Negative?** - IF condition on sentiment
7. **Simulate Email Notification** - Code node logging email details
8. **Log Non-Negative** - Code node for other sentiments
9. **Merge Branches** - Combines flows back
10. **No Tickets Found** - NoOp for empty results

## Environment Variables Required

Configure these in n8n Settings → Variables:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOi...
FASTAPI_URL=https://your-api.railway.app
FASTAPI_API_KEY=your-secret-key
SUPPORT_EMAIL=support@company.com
DASHBOARD_URL=https://dashboard.vercel.app
NOTIFICATION_FROM_EMAIL=noreply@company.com
```

## Credentials Required

### 1. Supabase Header Auth

**Name:** Supabase Header Auth
**Type:** Header Auth

**Headers:**
```
apikey: {{$env.SUPABASE_ANON_KEY}}
Authorization: Bearer {{$env.SUPABASE_ANON_KEY}}
```

**Setup:**
1. Go to Credentials → New Credential
2. Select "Header Auth"
3. Add header: `apikey` with value `={{$env.SUPABASE_ANON_KEY}}`
4. Add header: `Authorization` with value `=Bearer {{$env.SUPABASE_ANON_KEY}}`
5. Save as "Supabase Header Auth"

### 2. FastAPI Header Auth

**Name:** FastAPI Header Auth
**Type:** Header Auth

**Headers:**
```
X-API-Key: {{$env.FASTAPI_API_KEY}}
```

**Setup:**
1. Go to Credentials → New Credential
2. Select "Header Auth"
3. Add header: `X-API-Key` with value `={{$env.FASTAPI_API_KEY}}`
4. Save as "FastAPI Header Auth"

### 3. SMTP Account (Optional - for real emails)

**Type:** SMTP
**Only needed if using "Send Email Notification" node instead of simulation**

**Setup:**
1. Go to Credentials → New Credential
2. Select "SMTP"
3. Fill in your SMTP details:
   - Host: smtp.gmail.com (for Gmail)
   - Port: 587
   - Username: your-email@gmail.com
   - Password: your-app-password
4. Save as "SMTP Account"

## Import Instructions

### Step 1: Import Workflow

1. Open n8n
2. Click "+ Add Workflow"
3. Click "⋮" (three dots) → "Import from File"
4. Select `workflow.json`
5. Click "Import"

### Step 2: Configure Environment Variables

1. Go to Settings (gear icon) → Variables
2. Add all required variables (see above)
3. Save

### Step 3: Set Up Credentials

1. Click on "Get Unprocessed Tickets" node
2. Click "Create New Credential" under credentials
3. Follow "Supabase Header Auth" setup above
4. Repeat for "Call FastAPI Classifier" node with "FastAPI Header Auth"

### Step 4: Test Workflow

1. Click "Test Workflow" button
2. Check execution log for:
   - ✅ Supabase request successful
   - ✅ Tickets fetched (or empty array)
   - ✅ FastAPI call successful
   - ✅ Email simulation logged

### Step 5: Activate Workflow

1. Toggle "Active" switch (top right)
2. Workflow will now run every 60 seconds
3. Monitor executions in "Executions" tab

## Testing

### Test 1: Create Test Ticket in Supabase

```sql
INSERT INTO tickets (description)
VALUES ('Mi conexión a internet no funciona y estoy muy frustrado');
```

Wait 60 seconds for workflow to execute, check logs for:
- ✅ Ticket fetched
- ✅ FastAPI called
- ✅ Sentiment: Negativo
- ✅ Email simulation logged

### Test 2: Positive Sentiment

```sql
INSERT INTO tickets (description)
VALUES ('Excelente servicio, muchas gracias por la ayuda');
```

Check logs for:
- ✅ Sentiment: Positivo
- ✅ No email sent (Log Non-Negative executed)

## Troubleshooting

### Issue: No executions showing

**Solution:**
- Check workflow is activated (toggle in top-right)
- Check Schedule Trigger is configured correctly
- Wait at least 60 seconds for first execution

### Issue: "Supabase request failed"

**Solution:**
- Verify `SUPABASE_URL` is correct (include https://)
- Verify `SUPABASE_ANON_KEY` is the anon key (not service role)
- Check RLS policies allow read access to tickets table
- Test URL manually: `curl https://your-project.supabase.co/rest/v1/tickets?processed=eq.false`

### Issue: "FastAPI call failed"

**Solution:**
- Verify `FASTAPI_URL` is correct and accessible
- Verify `FASTAPI_API_KEY` matches API key in FastAPI .env
- Check FastAPI is deployed and running
- Test endpoint: `curl -X POST https://your-api.railway.app/health`

### Issue: No tickets found

**Solution:**
- Check tickets exist with `processed = false`
- Verify Supabase query parameters
- Check database connection

### Issue: Email simulation not showing

**Solution:**
- Check sentiment is actually "Negativo"
- Check IF node condition is correct
- View execution logs (click on node → View Execution Data)

## Switching to Real Email

To send real emails instead of simulation:

1. Set up SMTP credentials (see above)
2. In workflow, connect "Is Sentiment Negative?" TRUE branch to "Send Email Notification" instead of "Simulate Email Notification"
3. Delete or disconnect "Simulate Email Notification" node
4. Save and test

## Performance Tips

### Reduce Polling Frequency

If you have low ticket volume:
- Change Schedule Trigger to every 5 minutes
- Reduces API calls, saves resources

### Increase Batch Size

If you have high ticket volume:
- Change Split Into Items batch size to 5 or 10
- Processes multiple tickets in parallel

### Add Error Handling

Recommended additions:
- Error Trigger node
- Retry logic on FastAPI node (already configured)
- Dead letter queue for failed tickets

## Monitoring

### View Execution History

1. Click "Executions" in left sidebar
2. See all workflow runs
3. Click on execution to see details
4. Green = success, Red = error

### Key Metrics to Watch

- **Execution Count:** Should match polling frequency (e.g., 60/hour)
- **Success Rate:** Should be >99%
- **Processing Time:** Should be <10 seconds per ticket
- **Error Rate:** Should be <1%

### Logs Location

**Simulation Logs:**
- Node: "Simulate Email Notification"
- Output: Check execution data → View JSON output
- Console: Check n8n container logs

**Error Logs:**
- Executions tab → Click failed execution
- View error details

## Cost Optimization

### n8n Cloud Pricing

- **Starter:** 2,500 executions/month
- **Pro:** 10,000 executions/month

**Calculation:**
- 1 execution per minute = 1,440/day = 43,200/month
- Exceeds Starter plan → Use Pro plan or self-host

### Reduce Executions

**Option 1:** Poll less frequently
- Every 5 minutes = 8,640/month (fits Starter)

**Option 2:** Use webhook (see workflow-webhook.json)
- Only executes when ticket created
- Much lower execution count

## Support

For issues:
- Check n8n docs: https://docs.n8n.io
- n8n community: https://community.n8n.io
- GitHub issues: Repository issues tab

## Version History

- **v1.0** (2026-01-22) - Initial workflow
  - Schedule trigger
  - Supabase polling
  - FastAPI integration
  - Email simulation
  - Sentiment-based routing
