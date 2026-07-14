-- Reference schema for PostgreSQL (mirrors SQLAlchemy models)
-- Used by docker-compose on first container start.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risk_level') THEN
        CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alert_status') THEN
        CREATE TYPE alert_status AS ENUM ('pending', 'confirmed', 'dismissed');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'event_type') THEN
        CREATE TYPE event_type AS ENUM (
            'detection',
            'action',
            'alert',
            'human_intervention'
        );
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS cameras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    location VARCHAR(255) NOT NULL,
    zone VARCHAR(120),
    rtsp_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level risk_level NOT NULL UNIQUE,
    sensitivity DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    description VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS persons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(64) UNIQUE,
    label VARCHAR(120),
    embedding_path VARCHAR(512),
    is_suspicious BOOLEAN NOT NULL DEFAULT FALSE,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    person_id UUID REFERENCES persons(id) ON DELETE SET NULL,
    risk_level risk_level NOT NULL,
    action_type VARCHAR(120) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    reasoning TEXT,
    status alert_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID REFERENCES cameras(id) ON DELETE SET NULL,
    person_id UUID REFERENCES persons(id) ON DELETE SET NULL,
    event_type event_type NOT NULL,
    action_label VARCHAR(120),
    risk_level risk_level,
    location VARCHAR(255),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    human_intervention BOOLEAN NOT NULL DEFAULT FALSE,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO risk_profiles (level, sensitivity, description, settings)
VALUES
    ('low', 0.3, 'Low sensitivity — fewer alerts', '{"alert_delay_sec": 10}'::jsonb),
    ('medium', 0.6, 'Balanced monitoring', '{"alert_delay_sec": 5}'::jsonb),
    ('high', 0.9, 'High sensitivity — immediate alerts', '{"alert_delay_sec": 0}'::jsonb)
ON CONFLICT (level) DO NOTHING;
