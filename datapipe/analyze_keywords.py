"""
datapipe/analyze_keywords.py

- review 테이블에서 카메라 + 감성별로 리뷰를 모아
  간단한 키워드 분석(자주 등장하는 단어) 후
  review_keyword_stats 테이블에 저장.

실행 방법:

  cd datapipe
  source .venv/bin/activate
  python analyze_keywords.py
"""

import os
import re
from collections import Counter
from datetime import datetime

from sqlalchemy import create_engine, text


# ---------- DB 설정 ----------

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://devuser:devpass@localhost:5432/camera_reviews",
)
engine = create_engine(DB_URL, future=True)


# ---------- 간단 토큰화 / 불용어 ----------

# 너무 당연한 단어, 노이즈 단어는 제거 (원하는 대로 계속 추가 가능)
STOPWORDS = {
    "영상", "리뷰", "카메라", "사진", "후기",
    "진짜", "정말", "조금", "거의", "보고",
    "이거", "저거", "그냥", "사용", "사용기",
    "유튜브", "채널", "구독", "감사", "설명",
}


def tokenize(text: str):
    """
    매우 단순한 한국어 토큰화:
      - 특수문자 제거
      - 공백 기준 split
      - 1글자 토큰, 불용어 제거
    """
    if not text:
        return []

    # 한글/영어/숫자/공백만 남기고 나머지는 공백 처리
    text = re.sub(r"[^0-9가-힣A-Za-z\s]", " ", text)
    tokens = text.split()

    cleaned = []
    for tok in tokens:
        tok = tok.strip()
        if len(tok) <= 1:
            continue
        if tok in STOPWORDS:
            continue
        cleaned.append(tok)

    return cleaned


# ---------- 메인 로직 ----------

SELECT_SQL = text(
    """
    SELECT id, camera_model, sentiment_label, content
      FROM review
     WHERE sentiment_label IS NOT NULL
       AND TRIM(sentiment_label) <> ''
       AND camera_model IS NOT NULL
       AND TRIM(camera_model) <> ''
       AND content IS NOT NULL
       AND TRIM(content) <> ''
"""
)

DELETE_SQL = text("DELETE FROM review_keyword_stats")

INSERT_SQL = text(
    """
    INSERT INTO review_keyword_stats (
        camera_model, sentiment_label, keyword, freq, updated_at
    ) VALUES (
        :camera_model, :sentiment_label, :keyword, :freq, :updated_at
    )
"""
)


def main(top_k: int = 30):
    """
    카메라 기종 + 감성별로 top_k 키워드를 집계하여 review_keyword_stats에 저장
    """
    with engine.begin() as conn:
        rows = conn.execute(SELECT_SQL).mappings().all()
        print(f"🔎 키워드 분석 대상 리뷰 수: {len(rows)}")

        if not rows:
            print("분석할 리뷰가 없습니다.")
            return

        # (camera_model, sentiment_label) -> [content, content, ...]
        groups = {}
        for r in rows:
            key = (r["camera_model"], r["sentiment_label"])
            groups.setdefault(key, []).append(r["content"] or "")

        print(f"📂 카메라/감성 조합 개수: {len(groups)}")

        # 기존 통계 삭제
        conn.execute(DELETE_SQL)

        now = datetime.utcnow()
        total_inserted = 0

        for (camera, sentiment), contents in groups.items():
            counter = Counter()

            for content in contents:
                tokens = tokenize(content)
                counter.update(tokens)

            # 상위 top_k 개만 저장
            for keyword, freq in counter.most_common(top_k):
                conn.execute(
                    INSERT_SQL,
                    {
                        "camera_model": camera,
                        "sentiment_label": sentiment,
                        "keyword": keyword,
                        "freq": int(freq),
                        "updated_at": now,
                    },
                )
                total_inserted += 1

            print(
                f"  ▶ {camera} / {sentiment}: {len(counter)}개 토큰 중 상위 {top_k} 저장"
            )

    print(f"✅ 키워드 통계 업데이트 완료: 총 {total_inserted}행 삽입")


if __name__ == "__main__":
    main()