"""
datapipe/crawl_youtube_comments.py

사용 예:
  cd datapipe
  source .venv/bin/activate

  # Canon EOS R8
  python crawl_youtube_comments.py \
      --query "캐논 EOS R8 리뷰" \
      --camera "Canon EOS R8" \
      --max-videos 3 \
      --comments-per-video 40

설명:
 - query            : 유튜브 검색어 (한국어 키워드)
 - camera           : 이 실행에서 저장할 카메라 기종 이름
 - max-videos       : 검색해서 처리할 최대 비디오 수
 - comments-per-video : 비디오당 가져올 댓글 수
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

# DB URL
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

def is_noise_comment(text: str) -> bool:
    """
    리뷰와 무관한 '노이즈 댓글'을 필터링하는 함수.
    True  → noise로 간주 (DB INSERT 제외)
    False → 실제 리뷰 가능성이 있음
    
    단계:
      1) 너무 짧음
      2) 인사/감사 패턴
      3) 이모지/ㅋㅋ/ㅎㅎ 패턴
      4) 카메라 관련 키워드 없음
    """

    if not text:
        return True

    t = text.strip().lower()

    # ----- 1) 길이 기반 필터 (너무 짧은 댓글은 리뷰일 가능성 낮음)
    if len(t) < 10:
        return True
    
    # ----- 2) 인사/감사 패턴 필터
    NOISE_PATTERNS = [
        "잘 보고 갑니다", "잘봤습니다", "잘 봤습니다", 
        "영상 감사합니다", "감사합니다", "감사해요",
        "굿", "좋아요", "좋은 영상", "쿠팡",
        "고맙습니다", "덕분에", "수고하셨습니다", "?"
    ]
    for pat in NOISE_PATTERNS:
        if pat in t:
            return True

    # ----- 3) 거의 이모지/ㅋ/ㅎ 만 있는 댓글
    # 예: "ㅋㅋㅋㅋㅋㅋ", "ㅎㅎㅎㅎ", "🙏🙏😍"
    if re.fullmatch(r"[ㅋㅎㅠㅜ🙏❤️💜💙💚💛🤍🤎🖤⭐✨🔥\s]+", t):
        return True

    # ----- 4) 카메라 관련 키워드가 하나도 없으면 noise 가능성 ↑↑
    CAMERA_KEYWORDS = [
        "af", "오토포커스", "노이즈", "색감", "화이트밸런스",
        "화질", "디테일", "iso", "셔터", "조리개",
        "연사", "동영상", "발열", "손떨림", "ois", "렌즈",
        "고감도", "dr", "다이내믹", "초점", "트래킹",
        "센서", "바디", "프레임", "필름", "사진", "촬영",
        "흔들림", "저조도", "후지", "캐논", "소니", "니콘",
    ]

    if not any(k in t for k in CAMERA_KEYWORDS):
        return True

    # noise 아님 → 리뷰일 가능성 있음
    return False

def insert_reviews(rows, camera_model: str):
    """
    review 테이블에 INSERT
    - UNIQUE (source, content) 제약을 활용해 중복 기록 방지
    """
    if not rows:
        return 0

    sql = text("""
        INSERT INTO review (source, rating, content, created_at, camera_model)
        VALUES (:source, :rating, :content, :created_at, :camera_model)
        ON CONFLICT (source, content) DO NOTHING
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
                    "camera_model": camera_model,
                })
                inserted += 1
            except SQLAlchemyError as e:
                # 이 경우는 중복이 아닌 다른 오류
                print("[warn] DB insert error:", e)
    return inserted


def main(args):
    print(f"🔍 검색어: {args.query}")
    print(f"📷 카메라 기종: {args.camera}")
    print(f"   → 최대 비디오 {args.max_videos}개, 비디오당 댓글 {args.comments_per_video}개 수집 시도")

    video_ids = search_videos(args.query, max_results=args.max_videos)
    print("   검색된 비디오 수:", len(video_ids))

    total_inserted = 0

    for vid in tqdm(video_ids, desc="videos"):
        comments = fetch_comments_for_video(vid, max_comments=args.comments_per_video)

        rows = []
        for c in comments:
            text_clean = c["text"]

            # 노이즈 필터 적용
            if is_noise_comment(text_clean):
                continue

            rows.append({
                "source": f"youtube:{vid}",
                "content": c["text"],
                "created_at": c["publishedAt"],  # PostgreSQL이 ISO8601 자동 파싱
            })

        inserted = insert_reviews(rows, camera_model=args.camera)
        total_inserted += inserted
        time.sleep(0.2)  # rate-limit 완화

    print(f"✅ 총 삽입된 리뷰 개수: {total_inserted}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="유튜브 검색어 (예: '캐논 EOS R8 리뷰')")
    ap.add_argument("--camera", required=True, help="이 실행에서 수집할 카메라 기종 이름 (예: 'Canon EOS R8')")
    ap.add_argument("--max-videos", type=int, default=10, help="검색해서 처리할 최대 비디오 수")
    ap.add_argument("--comments-per-video", type=int, default=100, help="비디오당 최대 댓글 수")
    args = ap.parse_args()

    main(args)