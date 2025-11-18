-- docs/migration_003_reject_null_reviews.sql
-- 목적: content/camera_model 이 비어 있는 리뷰는 아예 INSERT 되지 않도록 막는 트리거 생성

-- 1) 트리거 함수 정의 (없으면 생성, 있으면 교체)
CREATE OR REPLACE FUNCTION reject_null_reviews()
RETURNS TRIGGER AS $$
BEGIN
  -- 내용이 없으면 삽입 취소
  IF NEW.content IS NULL OR trim(NEW.content) = '' THEN
    RETURN NULL; -- INSERT 자체를 스킵
  END IF;

  -- 카메라 기종이 없으면 삽입 취소
  IF NEW.camera_model IS NULL OR trim(NEW.camera_model) = '' THEN
    RETURN NULL;
  END IF;

  -- 위 조건에 안 걸리면 그대로 삽입
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2) 기존 트리거가 있다면 삭제
DROP TRIGGER IF EXISTS trg_reject_null ON review;

-- 3) BEFORE INSERT 트리거 등록
CREATE TRIGGER trg_reject_null
BEFORE INSERT ON review
FOR EACH ROW
EXECUTE FUNCTION reject_null_reviews();