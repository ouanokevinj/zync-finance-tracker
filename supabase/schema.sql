/*
 * Finance Tracker — Supabase schema
 * Run this in your Supabase project: SQL Editor → New query → paste → Run
 */

-- Earnings: income entries
CREATE TABLE earnings (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  amount     DECIMAL(12, 2) NOT NULL,
  source     VARCHAR(255)   NOT NULL,
  date       DATE           NOT NULL,
  created_at TIMESTAMP      DEFAULT NOW()
);

-- Subscriptions: recurring monthly charges
CREATE TABLE subscriptions (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name         VARCHAR(255)   NOT NULL,
  amount       DECIMAL(12, 2) NOT NULL,
  date_started DATE           NOT NULL,
  created_at   TIMESTAMP      DEFAULT NOW()
);

-- Spending: one-off purchases and expenses
CREATE TABLE spending (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  description VARCHAR(255)   NOT NULL,
  amount      DECIMAL(12, 2) NOT NULL,
  date        DATE           NOT NULL,
  created_at  TIMESTAMP      DEFAULT NOW()
);

-- Row Level Security: enabled but open for MVP (no auth)
ALTER TABLE earnings      ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE spending       ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public read/write earnings"
  ON earnings FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "public read/write subscriptions"
  ON subscriptions FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "public read/write spending"
  ON spending FOR ALL USING (true) WITH CHECK (true);
