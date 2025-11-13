ALTER TABLE review
    ADD COLUMN IF NOT EXISTS camera_model VARCHAR(100);

-- 기존 데이터는 일단 'Unknown'으로 채워두고,
-- 나중에 특정 카메라에 해당하는 리뷰만 있다면 여기서 한 번에 업데이트해도 됨.
UPDATE review
   SET camera_model = COALESCE(camera_model, 'Unknown');