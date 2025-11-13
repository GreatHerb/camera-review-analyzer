"""
datapipe/label_with_model.py

- review 테이블의 content 컬럼을 읽어서
- HuggingFace 감성 분석 모델로 예측
- sentiment_label / sentiment_score / sentiment_model 컬럼 채우기

여러 번 실행해도,
sentiment_model 이 비어있는 레코드만 처리하도록 설계되어 있습니다.
"""

from transformers import pipeline
from sqlalchemy import create_engine, text
import re

# 🔗 DB 연결 (기존과 동일)
engine = create_engine(
    "postgresql+psycopg2://devuser:devpass@localhost:5432/camera_reviews"
)

# 사용할 모델 (별점 라벨을 주는 멀티언어 모델)
MODEL_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"
clf = pipeline("sentiment-analysis", model=MODEL_NAME)

# '1 star' ~ '5 stars' 패턴
STAR_RE = re.compile(r"^\s*([1-5])\s*star", re.IGNORECASE)


def normalize_label(raw_label: str, score: float | None = None) -> str:
    """
    모델이 주는 라벨 문자열을 우리가 쓰는 3단계 감성으로 정규화.

    1) '1 star'~'5 stars' → negative / neutral / positive
    2) 'positive' / 'neutral' / 'negative' 같은 라벨도 수용
    3) 그 외 라벨은 score(신뢰도)를 기준으로 보수적으로 분류
    """
    if not raw_label:
        return "neutral"

    # 1. '4 stars' 같은 별점 패턴인 경우
    m = STAR_RE.match(raw_label)
    if m:
        n = int(m.group(1))
        if n <= 2:
            return "negative"
        if n == 3:
            return "neutral"
        return "positive"

    # 2. 이미 positive/neutral/negative처럼 오는 경우
    lower = raw_label.strip().lower()
    if lower in ("positive", "pos"):
        return "positive"
    if lower in ("neutral", "neu", "neutrality"):
        return "neutral"
    if lower in ("negative", "neg"):
        return "negative"

    # 3. 그 외 예외적인 라벨 → 점수 기준으로 보수적 처리
    if score is not None:
        if score >= 0.75:
            return "positive"
        if score <= 0.25:
            return "negative"

    return "neutral"


# 🎯 아직 모델 라벨을 달지 않은 레코드만 선별
SELECT_SQL = text("""
  SELECT id, content
    FROM review
   WHERE content IS NOT NULL
     AND TRIM(content) <> ''
     AND (sentiment_model IS NULL OR sentiment_model = '')
   ORDER BY id ASC
   LIMIT :batch
""")

UPDATE_SQL = text("""
  UPDATE review
     SET sentiment_label = :label,
         sentiment_score = :score,
         sentiment_model = :model
   WHERE id = :id
""")

BATCH_SIZE = 200  # 한 번에 처리할 레코드 수


def run_once() -> int:
    """
    한 번에 BATCH_SIZE 만큼만 처리.
    더 이상 처리 대상이 없으면 0을 반환.
    """
    updated = 0
    with engine.begin() as conn:
        rows = conn.execute(SELECT_SQL, {"batch": BATCH_SIZE}).mappings().all()
        if not rows:
            print("라벨링할 대상이 없습니다.")
            return 0

        for r in rows:
            text_in = (r["content"] or "").strip()
            if not text_in:
                continue
            try:
                res = clf(text_in)[0]    # 예: {'label': '4 stars', 'score': 0.65}
                raw_label = str(res.get("label", "")).strip()
                score = float(res.get("score", 0.0))
                label = normalize_label(raw_label, score)

                conn.execute(UPDATE_SQL, {
                    "id": r["id"],
                    "label": label,
                    "score": round(score, 3),
                    "model": MODEL_NAME,
                })
                updated += 1
            except Exception as e:
                # 한 건 에러나도 전체가 멈추지 않도록
                print(f"[warn] id={r['id']} inference error: {e}")
    return updated


if __name__ == "__main__":
    total = 0
    while True:
        n = run_once()
        total += n
        if n == 0:
            break
    print(f"✅ 모델 라벨링 완료: {total}건 업데이트")