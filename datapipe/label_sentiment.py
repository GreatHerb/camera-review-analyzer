from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg2://devuser:devpass@localhost:5432/camera_reviews")

# 아주 간단한 한국어 감정 단어 리스트(원하면 계속 확장 가능)
POSITIVE = {"좋아요", "만족", "추천", "가볍", "빠르", "선명", "훌륭", "괜찮"}
NEGATIVE = {"별로", "나쁘", "불만", "느리", "무겁", "노이즈", "아쉬", "실망", "심해"}

def label_of(text_ko: str) -> str:
    if not text_ko:
        return "neutral"
    t = text_ko.lower()
    pos_hit = any(w in t for w in POSITIVE)
    neg_hit = any(w in t for w in NEGATIVE)
    if pos_hit and not neg_hit:
        return "positive"
    if neg_hit and not pos_hit:
        return "negative"
    return "neutral"

select_sql = text("""
    SELECT id, content
    FROM review
    WHERE sentiment_label IS NULL
    ORDER BY id ASC
    LIMIT 1000
""")

update_sql = text("""
    UPDATE review
    SET sentiment_label = :label
    WHERE id = :id
""")

with engine.begin() as conn:
    rows = conn.execute(select_sql).mappings().all()
    for r in rows:
        label = label_of(r["content"] or "")
        conn.execute(update_sql, {"id": r["id"], "label": label})

print("라벨링 완료!")