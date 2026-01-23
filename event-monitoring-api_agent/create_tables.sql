CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS clients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  plan text DEFAULT 'free',
  contacts jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events (
  id bigserial PRIMARY KEY,
  client_id uuid NOT NULL REFERENCES clients(id),
  flow text NOT NULL,
  entity_type text NOT NULL,
  entity_id text NOT NULL,
  status text NOT NULL,
  severity text,
  message text,
  occurred_at timestamptz NOT NULL,
  meta jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS digests (
  id bigserial PRIMARY KEY,
  client_id uuid NOT NULL REFERENCES clients(id),
  window_start timestamptz NOT NULL,
  window_end timestamptz NOT NULL,
  stats jsonb NOT NULL,
  recommendations jsonb DEFAULT '{}'::jsonb,
  sent_at timestamptz
);

CREATE TABLE IF NOT EXISTS actions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id bigint NOT NULL REFERENCES events(id),
  client_id uuid NOT NULL REFERENCES clients(id),
  action_code text NOT NULL,
  mode text NOT NULL,  -- assist | auto
  request jsonb NOT NULL,
  response jsonb,
  status text NOT NULL DEFAULT 'proposed',
  created_at timestamptz DEFAULT now(),
  applied_at timestamptz,
  rolled_back_at timestamptz
);
