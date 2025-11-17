-- Migration: Add GDPR consent tracking fields
-- Date: 2025-10-23

-- Add consent fields to users table (idempotent)
ALTER TABLE users
ADD COLUMN IF NOT EXISTS cgu_accepted BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN IF NOT EXISTS privacy_policy_accepted BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN IF NOT EXISTS consent_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS account_deletion_requested BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS deletion_request_date TIMESTAMP;

-- Create index for faster consent queries (idempotent)
CREATE INDEX IF NOT EXISTS idx_users_consent ON users(cgu_accepted, privacy_policy_accepted);

-- Add comment for documentation
COMMENT ON COLUMN users.cgu_accepted IS 'Terms of use acceptance (required for GDPR)';
COMMENT ON COLUMN users.privacy_policy_accepted IS 'Privacy policy acceptance (required for GDPR)';
COMMENT ON COLUMN users.consent_date IS 'Date when user accepted CGU and privacy policy';
COMMENT ON COLUMN users.account_deletion_requested IS 'Flag for GDPR right to deletion';
COMMENT ON COLUMN users.deletion_request_date IS 'Date when user requested account deletion';
