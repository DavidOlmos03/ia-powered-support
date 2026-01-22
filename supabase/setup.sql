-- =====================================================
-- AI-Powered Support Co-Pilot - Database Setup
-- =====================================================
-- Description: Production-ready schema for ticket management system
-- Database: PostgreSQL 15+ (Supabase)
-- Author: Senior Data Engineer
-- Date: 2026-01-22
-- =====================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- ENUM TYPES
-- =====================================================

-- Category enum: Types of support tickets
CREATE TYPE category_enum AS ENUM (
    'Técnico',
    'Facturación',
    'Comercial'
);

-- Sentiment enum: Emotional tone of ticket
CREATE TYPE sentiment_enum AS ENUM (
    'Positivo',
    'Neutral',
    'Negativo'
);

-- =====================================================
-- MAIN TABLE: tickets
-- =====================================================

CREATE TABLE tickets (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Core ticket data
    description TEXT NOT NULL CHECK (char_length(description) >= 10),

    -- AI-generated classification (NULL until processed)
    category category_enum,
    sentiment sentiment_enum,

    -- Processing state tracking
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    processing_error TEXT,
    retry_count SMALLINT NOT NULL DEFAULT 0 CHECK (retry_count >= 0 AND retry_count <= 5),

    -- Metadata and source tracking
    source VARCHAR(50),
    metadata JSONB,

    -- Constraints
    CONSTRAINT valid_processing_timestamps CHECK (
        processing_completed_at IS NULL OR
        processing_completed_at >= processing_started_at
    ),
    CONSTRAINT valid_updated_timestamp CHECK (
        updated_at >= created_at
    )
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Index for finding unprocessed tickets (n8n polling)
CREATE INDEX idx_tickets_unprocessed
ON tickets (created_at DESC)
WHERE processed = FALSE;

-- Index for dashboard recent tickets query (covering index)
CREATE INDEX idx_tickets_recent
ON tickets (created_at DESC)
INCLUDE (category, sentiment, processed);

-- Index for analytics by category and sentiment
CREATE INDEX idx_tickets_classification
ON tickets (category, sentiment)
WHERE processed = TRUE;

-- Index for JSONB metadata queries
CREATE INDEX idx_tickets_metadata
ON tickets USING GIN (metadata);

-- Full-text search index on description (Spanish language)
CREATE INDEX idx_tickets_description_fts
ON tickets USING GIN (to_tsvector('spanish', description));

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at on every UPDATE
CREATE TRIGGER trigger_update_tickets_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to set processing timestamps
CREATE OR REPLACE FUNCTION set_processing_timestamps()
RETURNS TRIGGER AS $$
BEGIN
    -- If changing from unprocessed to processed, set started timestamp
    IF OLD.processed = FALSE AND NEW.processed = TRUE THEN
        IF NEW.processing_started_at IS NULL THEN
            NEW.processing_started_at = NOW();
        END IF;
        NEW.processing_completed_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-set processing timestamps
CREATE TRIGGER trigger_set_processing_timestamps
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION set_processing_timestamps();

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Enable RLS on tickets table
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;

-- Policy 1: Allow anonymous SELECT on all tickets (public dashboard)
CREATE POLICY "Allow public read access to all tickets"
ON tickets
FOR SELECT
TO anon
USING (true);

-- Policy 2: Allow authenticated users to SELECT all tickets
CREATE POLICY "Allow authenticated read access to all tickets"
ON tickets
FOR SELECT
TO authenticated
USING (true);

-- Policy 3: Allow authenticated users to INSERT tickets
CREATE POLICY "Allow authenticated users to create tickets"
ON tickets
FOR INSERT
TO authenticated
WITH CHECK (true);

-- Policy 4: Service role has full access (bypass RLS)
-- Note: service_role automatically bypasses RLS in Supabase

-- Policy 5: Allow authenticated users to UPDATE their own tickets (if user_id added later)
-- CREATE POLICY "Allow users to update their own tickets"
-- ON tickets
-- FOR UPDATE
-- TO authenticated
-- USING (auth.uid() = user_id)
-- WITH CHECK (auth.uid() = user_id);

-- =====================================================
-- REALTIME CONFIGURATION
-- =====================================================

-- Enable realtime for tickets table (Supabase specific)
-- This allows frontend to subscribe to INSERT/UPDATE events
ALTER TABLE tickets REPLICA IDENTITY FULL;

-- Publish changes to all operations
ALTER PUBLICATION supabase_realtime ADD TABLE tickets;

-- =====================================================
-- COMMENTS (Documentation)
-- =====================================================

COMMENT ON TABLE tickets IS 'Support tickets for AI-powered classification and sentiment analysis';

COMMENT ON COLUMN tickets.id IS 'Unique identifier (UUID v4)';
COMMENT ON COLUMN tickets.created_at IS 'Ticket creation timestamp (timezone-aware)';
COMMENT ON COLUMN tickets.updated_at IS 'Last modification timestamp (auto-updated)';
COMMENT ON COLUMN tickets.description IS 'Ticket content (min 10 characters)';
COMMENT ON COLUMN tickets.category IS 'AI-classified category: Técnico, Facturación, or Comercial';
COMMENT ON COLUMN tickets.sentiment IS 'AI-analyzed sentiment: Positivo, Neutral, or Negativo';
COMMENT ON COLUMN tickets.processed IS 'Whether ticket has been processed by AI (default: false)';
COMMENT ON COLUMN tickets.processing_started_at IS 'When AI processing began';
COMMENT ON COLUMN tickets.processing_completed_at IS 'When AI processing completed';
COMMENT ON COLUMN tickets.processing_error IS 'Error message if processing failed';
COMMENT ON COLUMN tickets.retry_count IS 'Number of processing retry attempts (max: 5)';
COMMENT ON COLUMN tickets.source IS 'Origin of ticket (e.g., web, api, email)';
COMMENT ON COLUMN tickets.metadata IS 'Flexible JSONB field for additional data';

-- =====================================================
-- INITIAL DATA (Optional - for testing)
-- =====================================================

-- Insert sample tickets for testing
INSERT INTO tickets (description, source) VALUES
    ('Mi conexión a internet no funciona desde hace 3 días. He reiniciado el router varias veces pero el problema persiste.', 'web'),
    ('Me han cobrado dos veces este mes en mi tarjeta de crédito. Necesito que revisen mi factura de inmediato.', 'web'),
    ('Estoy muy satisfecho con el servicio, solo quería agradecer al equipo de soporte por su excelente atención.', 'web'),
    ('¿Cómo puedo actualizar mi plan a la versión premium? Me interesa conocer los beneficios adicionales.', 'web'),
    ('El sistema está muy lento hoy, no puedo acceder a mi cuenta. Esto es muy frustrante.', 'api');

-- =====================================================
-- UTILITY VIEWS (Optional - for analytics)
-- =====================================================

-- View: Unprocessed tickets count
CREATE OR REPLACE VIEW v_unprocessed_count AS
SELECT COUNT(*) as unprocessed_tickets
FROM tickets
WHERE processed = FALSE;

-- View: Tickets by category and sentiment
CREATE OR REPLACE VIEW v_tickets_summary AS
SELECT
    category,
    sentiment,
    COUNT(*) as ticket_count,
    AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) as avg_processing_seconds
FROM tickets
WHERE processed = TRUE
GROUP BY category, sentiment
ORDER BY category, sentiment;

-- View: Recent tickets (last 100)
CREATE OR REPLACE VIEW v_recent_tickets AS
SELECT
    id,
    created_at,
    LEFT(description, 100) as description_preview,
    category,
    sentiment,
    processed,
    retry_count
FROM tickets
ORDER BY created_at DESC
LIMIT 100;

-- Grant SELECT on views to anon and authenticated roles
GRANT SELECT ON v_unprocessed_count TO anon, authenticated;
GRANT SELECT ON v_tickets_summary TO anon, authenticated;
GRANT SELECT ON v_recent_tickets TO anon, authenticated;

-- =====================================================
-- MAINTENANCE FUNCTIONS (Optional - for cleanup)
-- =====================================================

-- Function to archive old processed tickets (> 90 days)
CREATE OR REPLACE FUNCTION archive_old_tickets()
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- In production, this would move to archive table
    -- For now, just count what would be archived
    SELECT COUNT(*) INTO archived_count
    FROM tickets
    WHERE processed = TRUE
    AND created_at < NOW() - INTERVAL '90 days';

    -- TODO: Implement actual archival logic
    -- INSERT INTO tickets_archive SELECT * FROM tickets WHERE ...
    -- DELETE FROM tickets WHERE ...

    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Function to reset failed tickets for retry
CREATE OR REPLACE FUNCTION reset_failed_tickets()
RETURNS INTEGER AS $$
DECLARE
    reset_count INTEGER;
BEGIN
    UPDATE tickets
    SET
        processed = FALSE,
        retry_count = retry_count + 1,
        processing_error = NULL,
        processing_started_at = NULL,
        processing_completed_at = NULL
    WHERE processed = FALSE
    AND retry_count < 5
    AND processing_error IS NOT NULL
    AND created_at > NOW() - INTERVAL '7 days';

    GET DIAGNOSTICS reset_count = ROW_COUNT;
    RETURN reset_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Verify table structure
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'tickets'
-- ORDER BY ordinal_position;

-- Verify indexes
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'tickets';

-- Verify RLS policies
-- SELECT policyname, permissive, roles, cmd, qual
-- FROM pg_policies
-- WHERE tablename = 'tickets';

-- Test sample queries
-- SELECT * FROM tickets WHERE processed = FALSE ORDER BY created_at DESC LIMIT 10;
-- SELECT category, sentiment, COUNT(*) FROM tickets WHERE processed = TRUE GROUP BY category, sentiment;

-- =====================================================
-- END OF SETUP
-- =====================================================
