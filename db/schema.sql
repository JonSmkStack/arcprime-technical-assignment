CREATE TABLE disclosures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    docket_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    key_differences TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);