-- RedoClaim PostgreSQL initialization
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Performance indexes (created after SQLAlchemy creates tables)
-- These are run via a separate migration step
