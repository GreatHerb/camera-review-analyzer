"""
datapipe/crawl_youtube_comments.py

사용 예:
  cd datapipe
  source .venv/bin/activate
  python crawl_youtube_comments.py --query "카메라 리뷰" --max-videos 5 --comments-per-video 50

설명:
 - query: 유튜브 검색어 (한국어 키워드)
 - max-videos: 검색해서 처리할 최대 비디오 수
 - comments-per-video: 비디오당 가져올 댓글 수(상위 댓글 기준)
 - DB: camera_reviews 데이터베이스의 review 테이블에 INSERT
"""

import os
import time
import argparse
import html
import re

from googleapiclient.discovery import build
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from tqdm import tqdm

# ---- 설정 ----

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    raise RuntimeError("YOUTUBE_API_KEY 환경변수를 먼저 설정하세요.")

# DB URL: 기존과 동일
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://devuser:devpass@localhost:5432/camera_reviews"
)
engine = create_engine(DB_URL, future=True)

# YouTube API 클라이언트
yt = build("youtube", "v3", developerKey=YOUTUBE_API_KEY, cache_discovery=False)


def clean_text(s: str) -> str:
    """간단 텍스트 정제: HTML 엔티티, URL, 멘션 제거 + 공백 정리"""
    if not s:
        return s
    s = html.unescape(s)
    s = re.sub(r"https?://\S+", " ", s)        # URL 제거
    s = re.sub(r"@[A-Za-z0-9_]+", " ", s)      # 멘션 제거
    s = re.sub(r"\s+", " ", s).strip()
    return s


def search_videos(query: str, max_results: int = 20):
    """검색어로 유튜브 비디오 검색 후 videoId 리스트 반환"""
    video_ids = []
    next_page_token = None

    while len(video_ids) < max_results:
        resp = yt.search().list(
            q=query,
            part="id",
            type="video",
            maxResults=min(50, max_results - len(video_ids)),
            pageToken=next_page_token,
            relevanceLanguage="ko"
        ).execute()

        for item in resp.get("items", []):
            vid = item["id"]["videoId"]
            video_ids.append(vid)

        next_page_token = resp.get("nextPageToken")
        if not next_page_token:
            break

        time.sleep(0.1)

    return video_ids


def fetch_comments_for_video(video_id: str, max_comments: int = 200):
    """
    각 비디오의 top-level 댓글 수집
    반환: 리스트 of dict { 'video_id','text','publishedAt' }
    """
    comments = []
    next_token = None
    fetched = 0

    while fetched < max_comments:
        try:
            resp = yt.commentThreads().list(
                part="snippet",
                videoId=video_id,
                pageToken=next_token,
                maxResults=min(100, max_comments - fetched),
                textFormat="plainText"
            ).execute()
        except Exception as e:
            print(f"[warn] commentThreads 에러(video={video_id}):", e)
            break

        items = resp.get("items", [])
        if not items:
            break

        for it in items:
            s = it["snippet"]["topLevelComment"]["snippet"]
            text_raw = s.get("textDisplay", "")
            comment = {
                "video_id": video_id,
                "text": clean_text(text_raw),
                "publishedAt": s.get("publishedAt")
            }
            if comment["text"]:
                comments.append(comment)
                fetched += 1
                if fetched >= max_comments:
                    break

        next_token = resp.get("nextPageToken")
        if not next_token:
            break

        time.sleep(0.1)

    return comments


def insert_reviews(rows):
    """
    review 테이블에 INSERT
    가정: review 테이블 컬럼
      - id (serial)
      - source (text)
      - rating (int, nullable)
      - content (text)
      - created_at (timestamp without time zone, default now())
      - sentiment_label (text, nullable)
      - sentiment_score (numeric, nullable)
      - sentiment_model (text, nullable)
    """
    if not rows:
        return 0

    sql = text("""
        INSERT INTO review (source, rating, content, created_at)
        VALUES (:source, :rating, :content, :created_at)
    """)

    inserted = 0
    with engine.begin() as conn:
        for r in rows:
            try:
                conn.execute(sql, {
                    "source": r["source"],
                    "rating": None,
                    "content": r["content"],
                    "created_at": r["created_at"],
                })
                inserted += 1
            except SQLAlchemyError as e:
                print("[warn] DB insert error:", e)
    return inserted


def main(args):
    print(f"🔍 검색어: {args.query}")
    print(f"   → 최대 비디오 {args.max_videos}개, 비디오당 댓글 {args.comments_per_video}개 수집 시도")

    video_ids = search_videos(args.query, max_results=args.max_videos)
    print("   검색된 비디오 수:", len(video_ids))

    total_inserted = 0

    for vid in tqdm(video_ids, desc="videos"):
        comments = fetch_comments_for_video(vid, max_comments=args.comments_per_video)

        rows = []
        for c in comments:
            rows.append({
                "source": f"youtube:{vid}",
                "content": c["text"],
                # publishedAt는 ISO8601 형식이라 PostgreSQL이 그대로 파싱 가능
                "created_at": c["publishedAt"],
            })

        inserted = insert_reviews(rows)
        total_inserted += inserted
        time.sleep(0.2)  # rate limit 완화용

    print(f"✅ 총 삽입된 리뷰 개수: {total_inserted}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="유튜브 검색어 (예: '카메라 리뷰')")
    ap.add_argument("--max-videos", type=int, default=10, help="검색해서 처리할 최대 비디오 수")
    ap.add_argument("--comments-per-video", type=int, default=100, help="비디오당 최대 댓글 수")
    args = ap.parse_args()

    main(args)