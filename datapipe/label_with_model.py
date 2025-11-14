# datapipe/label_with_model.py

"""
한국어 전용 감성 분석 파이프라인

- 모델: WhitePeak/bert-base-cased-Korean-sentiment
  * LABEL_0: negative
  * LABEL_1: positive

- 우리의 매핑:
  * positive_prob >= 0.6  -> sentiment_label = "positive"
  * positive_prob <= 0.4  -> sentiment_label = "negative"
  * 나머지(중간 구간)    -> sentiment_label = "neutral"

- sentiment_score 컬럼에는 "positive 확률 (0~1)" 저장

사용 방법:
  cd datapipe
  source .venv/bin/activate
  python label_with_model.py
"""

import os
from typing import Tuple

from transformers import pipeline
from sqlalchemy import create_engine, text

# -----------------------------
# DB 설정
# -----------------------------
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://devuser:devpass@localhost:5432/camera_reviews"
)
engine = create_engine(DB_URL, future=True)

# -----------------------------
# 모델 설정
# -----------------------------
MODEL_NAME = "WhitePeak/bert-base-cased-Korean-sentiment"

# text-classification 파이프라인 생성
clf = pipeline(
    "text-classification",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME,
    # device를 따로 지정하지 않으면
    # 가능한 경우 MPS/GPU, 아니면 CPU를 자동 선택
)

# 1번에 처리할 최대 row 수 (너무 크게 할 필요 X)
BATCH_LIMIT = 128
MAX_LEN = 512  # BERT 최대 토큰 길이 (문자 기준 잘라서 사용)


# -----------------------------
# SQL 문
# -----------------------------
SELECT_SQL = text(f"""
  SELECT id, content
    FROM review
   WHERE content IS NOT NULL
     AND TRIM(content) <> ''
     AND (sentiment_model IS NULL OR sentiment_model = '')
   ORDER BY id ASC
   LIMIT {BATCH_LIMIT}
""")

UPDATE_SQL = text("""
  UPDATE review
     SET sentiment_label = :label,
         sentiment_score = :score,
         sentiment_model = :model
   WHERE id = :id
""")


# -----------------------------
# 헬퍼 함수들
# -----------------------------
def map_to_label(pred: dict) -> Tuple[str, float]:
    """
    HuggingFace pipeline 결과(pred)를
    (sentiment_label, positive_prob)로 변환.

    pred 예시:
      {
        "label": "LABEL_1",  # 또는 "LABEL_0"
        "score": 0.873...
      }

    LABEL_1: positive, LABEL_0: negative 라고 가정.
    """
    raw_label = pred["label"]
    score = float(pred["score"])

    # positive 확률 계산
    # LABEL_1 이면 score = positive 확률, 아니면 1 - score 로 변환
    if raw_label == "LABEL_1":
        positive_prob = score
    else:
        positive_prob = 1.0 - score

    # 구간 기반 레이블 결정
    if positive_prob >= 0.6:
        label = "positive"
    elif positive_prob <= 0.4:
        label = "negative"
    else:
        label = "neutral"

    return label, round(positive_prob, 3)


def classify_text(text_in: str) -> Tuple[str, float]:
    """
    단일 문장에 대해 감성 분석 수행 후
    (sentiment_label, positive_prob) 반환
    """
    # 길이가 너무 긴 경우 잘라서 사용 (토큰 512 넘어가는 문제 방지용)
    if len(text_in) > MAX_LEN:
        text_in = text_in[:MAX_LEN]

    # truncation / max_length 옵션을 줘서 tokenizer 단계에서 잘리도록
    pred = clf(text_in, truncation=True, max_length=MAX_LEN)[0]
    return map_to_label(pred)


# -----------------------------
# 메인 로직
# -----------------------------
def main():
    total_updated = 0

    with engine.begin() as conn:
        while True:
            rows = conn.execute(SELECT_SQL).mappings().all()
            if not rows:
                break

            print(f"🔎 이번 배치 라벨링 대상 행 수: {len(rows)}")

            for r in rows:
                text_raw = (r["content"] or "").strip()
                if not text_raw:
                    continue

                try:
                    label, prob = classify_text(text_raw)
                except Exception as e:
                    print(f"[warn] 모델 예측 중 오류(id={r['id']}): {e}")
                    continue

                conn.execute(
                    UPDATE_SQL,
                    {
                        "id": r["id"],
                        "label": label,
                        "score": prob,
                        "model": MODEL_NAME,
                    }
                )
                total_updated += 1

    print(f"✅ 모델 라벨링 완료: 총 {total_updated}건 업데이트")


if __name__ == "__main__":
    main()