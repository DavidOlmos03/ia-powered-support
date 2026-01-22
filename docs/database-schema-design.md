# Database Schema Design - Supabase (PostgreSQL)

**Role:** Senior Data Engineer
**Date:** 2026-01-22
**Database:** Supabase (PostgreSQL 15+)
**Project:** AI-Powered Support Co-Pilot

---

## 1. SCHEMA OVERVIEW

### Business Context
The `tickets` table is the core entity storing support requests that will be:
- Created by users/systems at high frequency
- Processed asynchronously by AI services
- Queried in real-time by dashboard clients
- Updated with classification results
- Potentially archived after resolution

### Design Goals
1. **Performance:** Fast inserts, efficient queries by status and time
2. **Scalability:** Support 100K+ tickets with consistent performance
3. **Integrity:** Prevent data corruption and maintain consistency
4. **Security:** Row-level access control for multi-tenant scenarios
5. **Observability:** Audit trail and processing metadata
6. **Extensibility:** Easy to add fields without breaking changes

---

## 2. TABLE STRUCTURE DESIGN

### Core Table: `tickets`

#### Column Specifications

| Column | Type | Constraints | Default | Rationale |
|--------|------|-------------|---------|-----------|
| `id` | `UUID` | PRIMARY KEY | `gen_random_uuid()` | Globally unique, distributed-friendly, no collision risk |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | `NOW()` | Timezone-aware for global operations |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | `NOW()` | Track last modification for auditing |
| `description` | `TEXT` | NOT NULL, CHECK(length > 10) | - | Unlimited length, validation for meaningful content |
| `category` | `category_enum` | NULL | NULL | Type-safe enum, NULL until processed |
| `sentiment` | `sentiment_enum` | NULL | NULL | Type-safe enum, NULL until processed |
| `processed` | `BOOLEAN` | NOT NULL | `FALSE` | Processing state flag |
| `processing_started_at` | `TIMESTAMPTZ` | NULL | NULL | Track processing latency |
| `processing_completed_at` | `TIMESTAMPTZ` | NULL | NULL | Calculate processing duration |
| `processing_error` | `TEXT` | NULL | NULL | Store error messages for debugging |
| `retry_count` | `SMALLINT` | NOT NULL, CHECK(retry_count >= 0) | `0` | Track retry attempts |
| `source` | `VARCHAR(50)` | NULL | NULL | Track ticket origin (web, api, email) |
| `metadata` | `JSONB` | NULL | NULL | Flexible storage for additional data |

#### Extended Analysis

**1. UUID vs BIGSERIAL for Primary Key**
- **Decision:** UUID (`gen_random_uuid()`)
- **Reasoning:**
  - Distributed system: n8n, FastAPI, Frontend all create/reference tickets
  - No central sequence bottleneck
  - Can generate IDs client-side if needed
  - No information leakage (SERIAL reveals record count)
  - Supabase Realtime works well with UUIDs
- **Trade-off:** 16 bytes vs 8 bytes (BIGINT), but negligible for expected scale

**2. TIMESTAMPTZ vs TIMESTAMP**
- **Decision:** TIMESTAMPTZ (timestamp with timezone)
- **Reasoning:**
  - Global application with potentially distributed users
  - Automatic timezone conversion
  - Prevents DST-related bugs
  - Standard for modern PostgreSQL applications

**3. TEXT vs VARCHAR for Description**
- **Decision:** TEXT
- **Reasoning:**
  - No length limit (tickets can be very detailed)
  - PostgreSQL stores both identically (TOAST mechanism)
  - TEXT is idiomatic in modern PostgreSQL
  - Easier to avoid "string too long" errors

**4. ENUM vs VARCHAR for Category/Sentiment**
- **Decision:** Custom ENUM types
- **Reasoning:**
  - Type safety at database level
  - Storage efficiency (4 bytes vs variable)
  - Query optimization (PostgreSQL knows all possible values)
  - Prevents typos ("Tecnico" vs "Técnico")
  - Self-documenting schema
- **Implementation:**
  ```
  CREATE TYPE category_enum AS ENUM ('Técnico', 'Facturación', 'Comercial');
  CREATE TYPE sentiment_enum AS ENUM ('Positivo', 'Neutral', 'Negativo');
  ```

**5. Additional Tracking Fields**
- `updated_at`: Track modifications for cache invalidation
- `processing_started_at` / `processing_completed_at`: Measure AI processing time
- `processing_error`: Debug failed classifications
- `retry_count`: Implement exponential backoff
- `source`: Analytics on ticket origins
- `metadata`: Extensibility without schema changes

---

## 3. ENUM TYPE DEFINITIONS

### category_enum
```
Values: 'Técnico', 'Facturación', 'Comercial'
```

**Design Considerations:**
- Matches business requirements exactly
- Spanish labels (as per requirements)
- Extensible: Can add values with `ALTER TYPE ... ADD VALUE`
- **Cannot remove values** (PostgreSQL limitation) - design accordingly

**Future Extension Strategy:**
- If categories need to be dynamic, migrate to lookup table
- Current ENUM is optimal for stable, small value sets (< 10 values)

### sentiment_enum
```
Values: 'Positivo', 'Neutral', 'Negativo'
```

**Design Considerations:**
- Three-point scale is standard for sentiment analysis
- Spanish labels for consistency
- Could extend to 5-point scale: 'Muy Positivo', 'Positivo', 'Neutral', 'Negativo', 'Muy Negativo'
- Keep simple initially, add granularity if needed

---

## 4. CONSTRAINTS & VALIDATIONS

### Primary Key
```
PRIMARY KEY (id)
```
- Automatic index creation
- Unique constraint enforcement
- Foreign key references (if adding related tables)

### NOT NULL Constraints
- `id`: Always required (auto-generated)
- `created_at`: Always required (auto-generated)
- `updated_at`: Always required (auto-generated)
- `description`: Business requirement - cannot process empty ticket
- `processed`: State machine requirement
- `retry_count`: Default 0, always known

### CHECK Constraints

**1. Description Length Validation**
```
CHECK (char_length(description) >= 10)
```
- Prevents spam/invalid tickets
- Ensures meaningful content for AI processing
- Adjust threshold based on real-world data

**2. Retry Count Validation**
```
CHECK (retry_count >= 0 AND retry_count <= 5)
```
- Prevents negative retries
- Cap at 5 to avoid infinite loops
- Move to dead-letter queue after max retries

**3. Processing State Consistency**
```
CHECK (
  (processed = FALSE AND category IS NULL AND sentiment IS NULL) OR
  (processed = TRUE AND category IS NOT NULL AND sentiment IS NOT NULL)
)
```
- Ensures atomic processing: either all fields set or none
- Prevents partial updates
- May be too strict if allowing manual overrides - consider removing

**4. Timestamp Logic Validation**
```
CHECK (processing_completed_at IS NULL OR processing_completed_at >= processing_started_at)
CHECK (updated_at >= created_at)
```
- Prevents time paradoxes
- Ensures data integrity

---

## 5. INDEXING STRATEGY

### Index Design Principles
1. **Index selective columns** used in WHERE clauses
2. **Composite indexes** for multi-column queries
3. **Partial indexes** for specific query patterns
4. **Avoid over-indexing** (slows writes, wastes space)

### Recommended Indexes

#### Index 1: Unprocessed Tickets Query
```
CREATE INDEX idx_tickets_unprocessed
ON tickets (created_at DESC)
WHERE processed = FALSE;
```
- **Use Case:** n8n polling for new tickets to process
- **Query Pattern:** `SELECT * FROM tickets WHERE processed = FALSE ORDER BY created_at DESC`
- **Type:** Partial index (smaller, faster)
- **Benefit:** 10-100x faster for unprocessed ticket queries

#### Index 2: Recent Tickets Dashboard
```
CREATE INDEX idx_tickets_recent
ON tickets (created_at DESC)
INCLUDE (category, sentiment, processed);
```
- **Use Case:** Dashboard loading recent tickets
- **Query Pattern:** `SELECT id, created_at, category, sentiment FROM tickets ORDER BY created_at DESC LIMIT 100`
- **Type:** Covering index (index-only scan)
- **Benefit:** No table access needed

#### Index 3: Category + Sentiment Analytics
```
CREATE INDEX idx_tickets_classification
ON tickets (category, sentiment)
WHERE processed = TRUE;
```
- **Use Case:** Analytics queries (count by category/sentiment)
- **Query Pattern:** `SELECT category, sentiment, COUNT(*) FROM tickets WHERE processed = TRUE GROUP BY category, sentiment`
- **Type:** Partial index on processed tickets
- **Benefit:** Fast aggregations for reporting

#### Index 4: JSONB Metadata Search
```
CREATE INDEX idx_tickets_metadata
ON tickets USING GIN (metadata);
```
- **Use Case:** Search within metadata JSON (e.g., custom fields)
- **Query Pattern:** `SELECT * FROM tickets WHERE metadata @> '{"priority": "high"}'`
- **Type:** GIN (Generalized Inverted Index) for JSONB
- **Benefit:** Enables flexible metadata queries

#### Index 5: Full-Text Search on Description
```
CREATE INDEX idx_tickets_description_fts
ON tickets USING GIN (to_tsvector('spanish', description));
```
- **Use Case:** Search tickets by keywords
- **Query Pattern:** `SELECT * FROM tickets WHERE to_tsvector('spanish', description) @@ to_tsquery('spanish', 'problema & conexión')`
- **Type:** GIN for full-text search
- **Benefit:** Fast text search without LIKE '%keyword%'
- **Language:** Spanish for better stemming and stop words

### Index Maintenance Considerations
- **Monitor index usage:** `pg_stat_user_indexes`
- **Remove unused indexes** after 30 days of no usage
- **Rebuild indexes** quarterly with `REINDEX CONCURRENTLY`
- **Vacuum regularly** to reclaim space

---

## 6. TRIGGERS & AUTOMATION

### Trigger 1: Auto-update `updated_at`
```
Purpose: Automatically set updated_at on every row modification
Type: BEFORE UPDATE trigger
```
- Standard pattern for audit trails
- Ensures updated_at is always accurate
- No application-level logic required

### Trigger 2: Processing State Transitions
```
Purpose: Set processing_started_at when processed changes to TRUE
Type: BEFORE UPDATE trigger
```
- Automatic tracking of processing timestamps
- Calculate SLA metrics (processing duration)

### Trigger 3: Supabase Realtime Broadcast
```
Purpose: Notify frontend of ticket changes
Type: AFTER INSERT/UPDATE trigger
```
- Built-in Supabase feature
- Enable with: `ALTER TABLE tickets REPLICA IDENTITY FULL;`
- Frontend subscribes to changes

---

## 7. ROW LEVEL SECURITY (RLS)

### Security Model

**Scenario 1: Public Dashboard (Read-Only)**
```
Policy: Allow anonymous users to SELECT processed tickets
```
- Public dashboard showing ticket statistics
- No authentication required
- Only show processed tickets

**Scenario 2: Authenticated Users (Create & Read Own)**
```
Policy: Users can INSERT their own tickets and SELECT their tickets
```
- User authentication via Supabase Auth
- Add `user_id UUID REFERENCES auth.users(id)` column
- Filter by `user_id = auth.uid()`

**Scenario 3: Service Role (Full Access)**
```
Policy: Service role (API key) has full access
```
- FastAPI uses service role key for updates
- n8n uses service role key for processing
- Bypass RLS with service_role

### RLS Policy Strategies

#### Strategy A: Simple Public Access (MVP)
- **Enable RLS:** `ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;`
- **Policy:** Allow all authenticated reads, service role writes
- **Best for:** Demo/MVP with trusted users

#### Strategy B: Multi-Tenant Isolation
- **Add column:** `organization_id UUID`
- **Policy:** Users only see tickets from their organization
- **Best for:** Production SaaS with multiple customers

#### Strategy C: Role-Based Access Control (RBAC)
- **Add column:** `created_by UUID, assigned_to UUID`
- **Policy:** Users see tickets they created or are assigned to
- **Best for:** Internal tools with different user roles

### Recommended for MVP: Strategy A
- Simple, secure enough for demo
- Easy to upgrade to Strategy B later
- Supabase anon key for frontend (read-only)
- Service role key for backend (read-write)

---

## 8. PARTITIONING STRATEGY

### When to Partition?
- **Current Scale:** Not needed for < 1M tickets
- **Future Scale:** Consider partitioning at 10M+ tickets
- **Query Pattern:** If mostly querying recent tickets (time-based)

### Partitioning Approach: Time-Based (Monthly)

#### Partition Key: `created_at`
```
Partition by RANGE (created_at)
Monthly partitions: tickets_2025_01, tickets_2025_02, etc.
```

#### Benefits
- **Query Performance:** Partition pruning for date range queries
- **Maintenance:** Drop old partitions instead of DELETE
- **Backup:** Partition-level backups
- **Archival:** Move old partitions to cold storage

#### Implementation Considerations
- **Overhead:** Adds complexity, only worth it at scale
- **Foreign Keys:** Limited support in partitioned tables
- **Indexes:** Must be created on each partition

### Recommendation
- **Phase 1 (0-100K tickets):** Single table, no partitioning
- **Phase 2 (100K-1M tickets):** Monitor query performance
- **Phase 3 (1M+ tickets):** Implement monthly partitioning

---

## 9. SCALABILITY CONSIDERATIONS

### Vertical Scaling (Supabase Tiers)

| Tier | Storage | Connections | Egress | Cost |
|------|---------|-------------|--------|------|
| Free | 500 MB | 60 | 2 GB | $0 |
| Pro | 8 GB | 200 | 250 GB | $25/mo |
| Team | 100 GB | 400 | 250 GB | $599/mo |

**Scaling Path:**
1. Start with Free tier (sufficient for MVP)
2. Upgrade to Pro when hitting 500MB or 60 connections
3. Pro tier supports 10M+ tickets with proper indexing

### Horizontal Scaling Patterns

#### Read Replicas
- Supabase supports read replicas on Team tier
- Route dashboard queries to replica
- Keep writes on primary

#### Connection Pooling
- Use PgBouncer (built-in Supabase)
- Transaction-level pooling for API requests
- Reduces connection overhead

#### Caching Layer
- Redis for frequently accessed data
- Cache processed ticket counts by category
- TTL: 5 minutes for real-time feel

### Storage Optimization

#### TOAST Table Management
- Large `description` fields stored in TOAST
- Automatic compression for > 2KB fields
- Consider external blob storage for attachments

#### Archive Strategy
```
Archive processed tickets older than 90 days
- Move to separate archive table
- Or export to data warehouse (BigQuery, Snowflake)
- Keep primary table lean (< 100K active tickets)
```

### Query Optimization

#### Materialized Views for Analytics
```
CREATE MATERIALIZED VIEW ticket_stats AS
SELECT
  DATE_TRUNC('day', created_at) AS day,
  category,
  sentiment,
  COUNT(*) as count,
  AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) as avg_processing_time
FROM tickets
WHERE processed = TRUE
GROUP BY 1, 2, 3;

CREATE UNIQUE INDEX ON ticket_stats (day, category, sentiment);
REFRESH MATERIALIZED VIEW CONCURRENTLY ticket_stats;
```
- Pre-aggregate statistics
- Refresh hourly via cron
- Dashboard queries materialized view (instant)

---

## 10. MONITORING & OBSERVABILITY

### Key Metrics to Track

#### Performance Metrics
- **Query Latency:** p50, p95, p99 for SELECT/INSERT/UPDATE
- **Index Hit Ratio:** Should be > 99%
- **Cache Hit Ratio:** Should be > 95%
- **Connection Pool Usage:** Monitor for saturation

#### Business Metrics
- **Ticket Volume:** Inserts per hour/day
- **Processing Rate:** Tickets processed per minute
- **Error Rate:** Failed processing attempts
- **Average Processing Time:** From created_at to processing_completed_at

### PostgreSQL Monitoring Queries

```sql
-- Index usage statistics
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE tablename = 'tickets'
ORDER BY idx_scan DESC;

-- Table bloat check
SELECT pg_size_pretty(pg_total_relation_size('tickets')) as total_size;

-- Slow queries (enable pg_stat_statements)
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
WHERE query LIKE '%tickets%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Alerts to Configure
- Table size > 400MB (80% of free tier)
- Unprocessed tickets > 100 (processing pipeline issue)
- Average processing time > 30s (performance degradation)
- Failed retry_count > 3 (systematic errors)

---

## 11. DATA LIFECYCLE MANAGEMENT

### Retention Policy

| State | Retention | Action |
|-------|-----------|--------|
| Unprocessed | 7 days | Auto-retry or move to failed queue |
| Processed | 90 days | Keep in hot storage |
| Archived | 1 year | Move to cold storage |
| Historical | Forever | Data warehouse for analytics |

### Backup Strategy
- **Point-in-Time Recovery (PITR):** 7 days (Supabase Pro)
- **Daily Snapshots:** Keep 30 days
- **Monthly Archives:** Export to S3/GCS

### GDPR Compliance Considerations
- Add `deleted_at` column for soft deletes
- Implement hard delete after 30 days
- Anonymize personal data in archived tickets
- Provide data export functionality

---

## 12. MIGRATION & VERSIONING STRATEGY

### Schema Versioning
- Use migration tools: Supabase Migrations, Flyway, or dbmate
- Each change is a versioned migration file
- Track schema version in `schema_migrations` table

### Safe Migration Patterns

#### Adding Nullable Columns (Safe)
```
ALTER TABLE tickets ADD COLUMN priority VARCHAR(20);
```
- No impact on existing rows
- No downtime required

#### Adding NOT NULL Columns (Requires Backfill)
```
Step 1: ADD COLUMN priority VARCHAR(20);
Step 2: UPDATE tickets SET priority = 'medium' WHERE priority IS NULL;
Step 3: ALTER TABLE tickets ALTER COLUMN priority SET NOT NULL;
```
- Backfill in batches to avoid locks

#### Changing ENUM Values (Complex)
```
Cannot remove ENUM values in PostgreSQL
Workaround: Create new ENUM, migrate data, drop old column
```

### Zero-Downtime Deployment
1. **Expand Phase:** Add new columns/indexes
2. **Migrate Phase:** Dual-write to old and new
3. **Contract Phase:** Remove old columns/indexes

---

## 13. TESTING STRATEGY

### Unit Tests (Database Level)
- Test CHECK constraints with invalid data
- Test triggers fire correctly
- Test RLS policies enforce security

### Performance Tests
- Load test: 1000 inserts/second
- Query test: SELECT with 1M rows
- Concurrent update test: 100 simultaneous updates

### Data Quality Tests
- No NULL in NOT NULL columns
- All processed tickets have category/sentiment
- No orphaned records

---

## 14. FUTURE ENHANCEMENTS

### Phase 2 Features

**1. Ticket Relationships**
```
Add columns: parent_ticket_id, related_ticket_ids[]
```
- Link duplicate tickets
- Track ticket escalations

**2. Conversation History**
```
New table: ticket_messages
```
- Support multi-turn conversations
- Store AI agent responses

**3. Attachments**
```
New table: ticket_attachments
```
- Store file uploads separately
- Reference from tickets table

**4. Audit Log**
```
New table: ticket_audit_log
```
- Track all changes (who, when, what)
- Compliance and debugging

**5. SLA Tracking**
```
Add columns: sla_due_at, sla_breached
```
- Track response time SLAs
- Alert on SLA violations

---

## 15. DESIGN SUMMARY

### Final Schema Overview

**Table:** `tickets`
- **Columns:** 13 (6 required, 7 nullable)
- **Indexes:** 5 (1 primary, 4 secondary)
- **Constraints:** 4 CHECK constraints
- **Triggers:** 2 (updated_at, processing_timestamps)
- **RLS:** Enabled with service role bypass
- **Partitioning:** None initially, plan for 1M+ tickets

### Key Design Decisions
1. ✅ UUID primary key for distributed systems
2. ✅ ENUM types for type-safe categories/sentiment
3. ✅ TIMESTAMPTZ for global timezone support
4. ✅ JSONB metadata for extensibility
5. ✅ Partial indexes for efficient queries
6. ✅ Full-text search for Spanish content
7. ✅ Processing tracking columns for observability
8. ✅ Retry mechanism with bounded attempts

### Storage Estimation
- **Per Ticket:** ~500 bytes (without description)
- **With 100-char description:** ~650 bytes
- **100K tickets:** ~65 MB
- **1M tickets:** ~650 MB (approaching Free tier limit)

### Performance Targets
- **Insert:** < 10ms (p95)
- **SELECT unprocessed:** < 50ms (p95)
- **UPDATE processed:** < 20ms (p95)
- **Dashboard load (100 tickets):** < 100ms (p95)

---

## NEXT STEPS

1. ✅ Review this design with team
2. ⏭ Create `setup.sql` implementation file
3. ⏭ Write database migration scripts
4. ⏭ Implement RLS policies
5. ⏭ Set up monitoring dashboards
6. ⏭ Load test with synthetic data
7. ⏭ Document API access patterns
