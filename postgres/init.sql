-- Runs on first container start.
-- SQLAlchemy creates the tables via ORM (init_db on startup).
-- Use this for extensions or seed data.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
