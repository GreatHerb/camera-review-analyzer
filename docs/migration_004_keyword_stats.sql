-- docs/migration_004_keyword_stats.sql
-- 목적: 카메라 기종 + 감성 라벨별 키워드 통계 저장용 테이블 생성

CREATE TABLE IF NOT EXISTS review_keyword_stats (
    id BIGSERIAL PRIMARY KEY,
    camera_model     TEXT NOT NULL,
    sentiment_label  TEXT NOT NULL,
    keyword          TEXT NOT NULL,
    freq             INTEGER NOT NULL,
    updated_at       TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

-- 조회 최적화를 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_rks_cam_sent
    ON review_keyword_stats (camera_model, sentiment_label);

CREATE INDEX IF NOT EXISTS idx_rks_keyword
    ON review_keyword_stats (keyword);