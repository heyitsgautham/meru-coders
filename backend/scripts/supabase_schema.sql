-- ================================================
-- Supabase Database Schema for Meru Coders
-- Chandas Identifier - SIH 2025
-- ================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================
-- 1. USERS TABLE
-- ================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    full_name TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast username lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);

-- ================================================
-- 2. VERSES TABLE (Migrated from CSVs)
-- ================================================
CREATE TABLE IF NOT EXISTS verses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    verse_text TEXT NOT NULL,
    verse_text_transliterated TEXT, -- IAST or SLP1 version
    meter TEXT NOT NULL, -- Chandas name (Devanagari)
    meter_iast TEXT, -- IAST version of meter name
    lg_pattern TEXT, -- Laghu-Guru pattern
    syllable_count INTEGER,
    source TEXT NOT NULL, -- 'rigveda', 'chandovallari', 'vedanga', etc.
    metadata JSONB, -- mandala, sukta, rik, seer, divinity, etc.
    is_approved BOOLEAN DEFAULT TRUE, -- For existing data: true, for user contributions: false
    contributed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_verses_meter ON verses(meter);
CREATE INDEX IF NOT EXISTS idx_verses_source ON verses(source);
CREATE INDEX IF NOT EXISTS idx_verses_is_approved ON verses(is_approved);
CREATE INDEX IF NOT EXISTS idx_verses_contributed_by ON verses(contributed_by);
CREATE INDEX IF NOT EXISTS idx_verses_syllable_count ON verses(syllable_count);

-- Full-text search index on verse_text (for future search functionality)
-- Using 'simple' config since 'sanskrit' doesn't exist in Supabase
CREATE INDEX IF NOT EXISTS idx_verses_text_search ON verses USING gin(to_tsvector('simple', verse_text));

-- ================================================
-- 3. METER DEFINITIONS TABLE
-- ================================================
CREATE TABLE IF NOT EXISTS meter_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meter_name_devanagari TEXT NOT NULL,
    meter_name_iast TEXT,
    category TEXT NOT NULL, -- 'sama', 'vishama', 'ardhasama', 'matra', 'jaati', 'vedic'
    lg_pattern TEXT,
    syllable_count INTEGER,
    matra_count TEXT, -- Can be multi-digit like "12181215"
    pada_number INTEGER,
    yati TEXT, -- Caesura position
    gana TEXT, -- Gana representation
    metadata JSONB, -- Any additional properties from CSV
    description TEXT, -- Human-readable explanation
    is_approved BOOLEAN DEFAULT TRUE,
    contributed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_meter_definitions_name_devanagari ON meter_definitions(meter_name_devanagari);
CREATE INDEX IF NOT EXISTS idx_meter_definitions_category ON meter_definitions(category);
CREATE INDEX IF NOT EXISTS idx_meter_definitions_is_approved ON meter_definitions(is_approved);
CREATE INDEX IF NOT EXISTS idx_meter_definitions_contributed_by ON meter_definitions(contributed_by);

-- ================================================
-- 4. PENDING CONTRIBUTIONS TABLE
-- ================================================
CREATE TABLE IF NOT EXISTS pending_contributions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contribution_type TEXT NOT NULL CHECK (contribution_type IN ('verse', 'meter_definition')),
    data JSONB NOT NULL, -- The submitted data
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    submitted_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    review_notes TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pending_contributions_status ON pending_contributions(status);
CREATE INDEX IF NOT EXISTS idx_pending_contributions_submitted_by ON pending_contributions(submitted_by);
CREATE INDEX IF NOT EXISTS idx_pending_contributions_type ON pending_contributions(contribution_type);

-- ================================================
-- 5. USER ACTIVITY LOG (Optional - for analytics)
-- ================================================
CREATE TABLE IF NOT EXISTS user_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    activity_type TEXT NOT NULL, -- 'login', 'contribution', 'analysis', etc.
    activity_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_created_at ON user_activity(created_at);

-- ================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE verses ENABLE ROW LEVEL SECURITY;
ALTER TABLE meter_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_contributions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity ENABLE ROW LEVEL SECURITY;

-- ================================================
-- USERS TABLE POLICIES
-- ================================================

-- Anyone can read users (for display names, etc.)
CREATE POLICY "Users are viewable by everyone"
ON users FOR SELECT
USING (true);

-- Users can update their own profile
CREATE POLICY "Users can update their own profile"
ON users FOR UPDATE
USING (auth.uid() = id);

-- ================================================
-- VERSES TABLE POLICIES
-- ================================================

-- Anyone can read approved verses
CREATE POLICY "Approved verses are viewable by everyone"
ON verses FOR SELECT
USING (is_approved = true OR contributed_by = auth.uid());

-- Authenticated users can insert verses (as pending)
CREATE POLICY "Authenticated users can insert verses"
ON verses FOR INSERT
WITH CHECK (auth.role() = 'authenticated' AND contributed_by = auth.uid());

-- Users can update their own pending verses
CREATE POLICY "Users can update their own pending verses"
ON verses FOR UPDATE
USING (contributed_by = auth.uid() AND is_approved = false);

-- Admins can approve/reject any verse
CREATE POLICY "Admins can update any verse"
ON verses FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid() AND users.is_admin = true
    )
);

-- ================================================
-- METER DEFINITIONS TABLE POLICIES
-- ================================================

-- Anyone can read approved meter definitions
CREATE POLICY "Approved meter definitions are viewable by everyone"
ON meter_definitions FOR SELECT
USING (is_approved = true OR contributed_by = auth.uid());

-- Authenticated users can insert meter definitions
CREATE POLICY "Authenticated users can insert meter definitions"
ON meter_definitions FOR INSERT
WITH CHECK (auth.role() = 'authenticated' AND contributed_by = auth.uid());

-- Users can update their own pending definitions
CREATE POLICY "Users can update their own pending definitions"
ON meter_definitions FOR UPDATE
USING (contributed_by = auth.uid() AND is_approved = false);

-- Admins can update any meter definition
CREATE POLICY "Admins can update any meter definition"
ON meter_definitions FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid() AND users.is_admin = true
    )
);

-- ================================================
-- PENDING CONTRIBUTIONS TABLE POLICIES
-- ================================================

-- Users can view their own contributions
CREATE POLICY "Users can view their own contributions"
ON pending_contributions FOR SELECT
USING (submitted_by = auth.uid());

-- Admins can view all contributions
CREATE POLICY "Admins can view all contributions"
ON pending_contributions FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid() AND users.is_admin = true
    )
);

-- Authenticated users can insert contributions
CREATE POLICY "Authenticated users can insert contributions"
ON pending_contributions FOR INSERT
WITH CHECK (auth.role() = 'authenticated' AND submitted_by = auth.uid());

-- Admins can update contribution status
CREATE POLICY "Admins can update contributions"
ON pending_contributions FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid() AND users.is_admin = true
    )
);

-- ================================================
-- USER ACTIVITY TABLE POLICIES
-- ================================================

-- Users can view their own activity
CREATE POLICY "Users can view their own activity"
ON user_activity FOR SELECT
USING (user_id = auth.uid());

-- Admins can view all activity
CREATE POLICY "Admins can view all activity"
ON user_activity FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid() AND users.is_admin = true
    )
);

-- Anyone can insert activity (for logging)
CREATE POLICY "Anyone can insert activity"
ON user_activity FOR INSERT
WITH CHECK (true);

-- ================================================
-- FUNCTIONS AND TRIGGERS
-- ================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_verses_updated_at BEFORE UPDATE ON verses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meter_definitions_updated_at BEFORE UPDATE ON meter_definitions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================
-- ADMIN USER CREATION
-- ================================================
-- NOTE: Admin credentials are hardcoded in backend:
-- Username: admin-erase-sure
-- Password: Pazz!$79UNO
-- 
-- After admin signs up via Supabase Auth, run:
-- UPDATE users SET is_admin = true WHERE username = 'admin-erase-sure';

-- ================================================
-- MIGRATION LOG TABLE (for CSV import tracking)
-- ================================================
CREATE TABLE IF NOT EXISTS migration_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    migration_name TEXT NOT NULL,
    source_file TEXT NOT NULL,
    records_migrated INTEGER NOT NULL,
    migration_status TEXT DEFAULT 'success' CHECK (migration_status IN ('success', 'partial', 'failed')),
    error_message TEXT,
    migrated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_migration_log_migration_name ON migration_log(migration_name);
CREATE INDEX IF NOT EXISTS idx_migration_log_migrated_at ON migration_log(migrated_at DESC);

COMMENT ON TABLE migration_log IS 'Tracks CSV to Supabase migrations with rollback capability';

-- ================================================
-- GRANT PERMISSIONS (if using service role)
-- ================================================
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, authenticated, service_role;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, authenticated, service_role;

-- ================================================
-- COMPLETION
-- ================================================
-- Database schema created successfully!
-- Next steps:
-- 1. Run this SQL in Supabase SQL Editor
-- 2. Run the migration script to import CSV data
-- 3. Create admin user and set is_admin = true
