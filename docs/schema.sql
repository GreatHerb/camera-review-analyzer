CREATE TABLE IF NOT EXISTS review (
  id SERIAL PRIMARY KEY,
  source  TEXT,
  rating  NUMERIC(2,1),
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);