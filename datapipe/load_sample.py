from sqlalchemy import create_engine, text
from datetime import datetime

rows = [
    {"source": "sample", "rating": 4.5, "content": "AF가 빠르고 가벼워서 좋아요."},
    {"source": "sample", "rating": 2.0, "content": "저조도에서 노이즈가 심해요."},
    {"source": "sample", "rating": 4.0, "content": "색감이 만족스럽고 휴대성도 좋아요."},
]

engine = create_engine("postgresql+psycopg2://devuser:devpass@localhost:5432/camera_reviews")

insert_sql = text("""
    INSERT INTO review (source, rating, content, created_at)
    VALUES (:source, :rating, :content, :created_at)
""")

# executemany 스타일: 리스트-오브-딕셔너리로 한 번에
payload = [
    {
        "source": r["source"],
        "rating": r["rating"],
        "content": r["content"],
        "created_at": datetime.now(),
    }
    for r in rows
]

with engine.begin() as conn:
    conn.execute(insert_sql, payload)

print("샘플 리뷰 3건 적재 완료!")