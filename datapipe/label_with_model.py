from transformers import pipeline
from sqlalchemy import create_engine, text

# DB 연결
engine = create_engine("postgresql+psycopg2://devuser:devpass@localhost:5432/camera_reviews")

# 멀티언어 감성 모델 (별점 기반) — 한국어도 잘 처리
clf = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

def stars_to_label(stars: str) -> str:
    """
    모델 라벨 예: '1 star' ~ '5 stars'
    1~2 -> negative, 3 -> neutral, 4~5 -> positive
    """
    n = int(stars.split()[0])
    if n <= 2:
        return "negative"
    if n == 3:
        return "neutral"
    return "positive"

# 아직 모델 라벨을 달지 않은 레코드만 처리
SELECT_SQL = text("""
  SELECT id, content
    FROM review
   WHERE content IS NOT NULL AND TRIM(content) <> ''
     AND (sentiment_model IS NULL OR sentiment_model = '')
   ORDER BY id ASC
   LIMIT 200
""")

UPDATE_SQL = text("""
  UPDATE review
     SET sentiment_label = :label,
         sentiment_score = :score,
         sentiment_model = :model
   WHERE id = :id
""")

MODEL_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"

with engine.begin() as conn:
    rows = conn.execute(SELECT_SQL).mappings().all()
    if not rows:
        print("라벨링할 대상이 없습니다.")
    count = 0
    for r in rows:
        text_in = (r["content"] or "").strip()
        if not text_in:
            continue
        res = clf(text_in)[0]              # 예: {'label': '4 stars', 'score': 0.65}
        label = stars_to_label(res["label"])
        score = round(float(res["score"]), 3)
        conn.execute(UPDATE_SQL, {
            "id": r["id"],
            "label": label,
            "score": score,
            "model": MODEL_NAME
        })
        count += 1

print(f"✅ 모델 라벨링 완료: {count}건 업데이트")