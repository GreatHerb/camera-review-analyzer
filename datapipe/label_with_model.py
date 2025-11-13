"""
datapipe/label_with_model.py

- review 테이블에서 아직 감성 라벨이 없는 행들을 가져와
  HuggingFace 모델로 감성 분석 후 sentiment_label / sentiment_score / sentiment_model 컬럼을 업데이트.

실행 방법 (단독):

  cd datapipe
  source .venv/bin/activate
  python label_with_model.py
"""

import os
from transformers import pipeline
from sqlalchemy import create_engine, text


# ---------- DB & 모델 설정 ----------

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://devuser:devpass@localhost:5432/camera_reviews",
)
engine = create_engine(DB_URL, future=True)

MODEL_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"

# 멀티언어 감성 모델 (1~5 stars 라벨 반환)
clf = pipeline(
    "sentiment-analysis",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME,
    truncation=True,   # 🔹 길면 자동으로 잘라줌
    max_length=512,    # 🔹 최대 512 토큰
)


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


# 아직 감성 정보가 비어 있는 행들만 선택
SELECT_SQL = text(
    """
    SELECT id, content
      FROM review
     WHERE content IS NOT NULL
       AND TRIM(content) <> ''
       AND (
            sentiment_label IS NULL OR sentiment_label = ''
            OR sentiment_model IS NULL OR sentiment_model = ''
       )
     ORDER BY id ASC
"""
)

UPDATE_SQL = text(
    """
    UPDATE review
       SET sentiment_label = :label,
           sentiment_score = :score,
           sentiment_model = :model
     WHERE id = :id
"""
)


def main():
    """한 번 전체 라벨링 수행"""
    with engine.begin() as conn:
        rows = conn.execute(SELECT_SQL).mappings().all()
        total = len(rows)
        print(f"🔎 라벨링 대상 행 수: {total}")

        if total == 0:
            print("라벨링할 대상이 없습니다.")
            return

        count = 0
        MAX_CHARS = 1000  # 너무 길면 그냥 앞부분만 사용 (안전장치)

        for r in rows:
            text_in = (r["content"] or "").strip()
            if not text_in:
                continue

            # 🔹 아주 긴 댓글이면 앞 부분만 사용 (BERT 한계 보호)
            if len(text_in) > MAX_CHARS:
                text_in = text_in[:MAX_CHARS]

            try:
                # 예: {'label': '4 stars', 'score': 0.65}
                res = clf(text_in)[0]
            except Exception as e:
                print(f"[warn] 감성 분석 실패 (id={r['id']}): {e}")
                # 이 한 줄은 건너뛰고 다음 리뷰로
                continue

            label = stars_to_label(res["label"])
            score = round(float(res["score"]), 3)

            conn.execute(
                UPDATE_SQL,
                {
                    "id": r["id"],
                    "label": label,
                    "score": score,
                    "model": MODEL_NAME,
                },
            )
            count += 1

    print(f"✅ 모델 라벨링 완료: {count}건 업데이트")


if __name__ == "__main__":
    main()