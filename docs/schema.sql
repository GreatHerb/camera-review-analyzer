CREATE TABLE IF NOT EXISTS review (
  id SERIAL PRIMARY KEY,
  source  TEXT,
  rating  NUMERIC(2,1),
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 감성 라벨 컬럼 추가
ALTER TABLE review
ADD COLUMN IF NOT EXISTS sentiment_label VARCHAR(16);

-- 조회/집계 최적화를 위한 인덱스(선택)
CREATE INDEX IF NOT EXISTS idx_review_created_at ON review (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_review_sentiment ON review (sentiment_label);