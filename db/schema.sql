-- Disclosures table
CREATE TABLE disclosures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    docket_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    key_differences TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'approved', 'rejected')),
    original_filename TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inventors table
CREATE TABLE inventors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    disclosure_id UUID NOT NULL REFERENCES disclosures(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sequence for docket numbers
CREATE SEQUENCE docket_seq START 1;

-- Index for faster lookups
CREATE INDEX idx_inventors_disclosure_id ON inventors(disclosure_id);
CREATE INDEX idx_disclosures_status ON disclosures(status);
CREATE INDEX idx_disclosures_created_at ON disclosures(created_at DESC);
