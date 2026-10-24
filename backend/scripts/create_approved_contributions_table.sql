-- Create approved_contributions table for storing approved user submissions
-- Run this in Supabase SQL Editor: https://app.supabase.com/project/_/editor

-- Drop existing table if it has wrong foreign key constraints
DROP TABLE IF EXISTS approved_contributions CASCADE;

CREATE TABLE IF NOT EXISTS approved_contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contribution_type TEXT NOT NULL CHECK (contribution_type IN ('verse', 'meter_definition')),
    data JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'approved' CHECK (status IN ('approved', 'published')),
    
    -- User tracking - FIXED: Reference users table, not auth.users
    submitted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Metadata
    review_notes TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_approved_contributions_type ON approved_contributions(contribution_type);
CREATE INDEX idx_approved_contributions_submitted_by ON approved_contributions(submitted_by);
CREATE INDEX idx_approved_contributions_status ON approved_contributions(status);
CREATE INDEX idx_approved_contributions_submitted_at ON approved_contributions(submitted_at DESC);

-- Enable RLS (Row Level Security)
ALTER TABLE approved_contributions ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can read approved contributions
CREATE POLICY "Anyone can read approved contributions"
ON approved_contributions FOR SELECT
TO authenticated, anon
USING (true);

-- Policy: Only admins can insert/update/delete
CREATE POLICY "Only admins can modify approved contributions"
ON approved_contributions FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid()
        AND users.is_admin = true
    )
);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_approved_contributions_updated_at
    BEFORE UPDATE ON approved_contributions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment
COMMENT ON TABLE approved_contributions IS 'Stores user-contributed verses and meter definitions that have been approved by admins';
