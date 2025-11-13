"""
datapipe/batch_crawl_cameras.py

여기 파일 안의 CAMERA_JOBS 리스트만 수정해서
여러 카메라 기종에 대해 한 번에 크롤링할 수 있는 스크립트.

사용 방법:

  cd datapipe
  source .venv/bin/activate
  python batch_crawl_cameras.py

사전 준비:
  - YOUTUBE_API_KEY 환경변수 설정 필요
  - crawl_youtube_comments.py 에서 DB 연결/트리거 등은 이미 세팅되어 있다고 가정
"""

from dataclasses import dataclass
from typing import List

# 기존 크롤러의 main 함수를 재사용
from crawl_youtube_comments import main as crawl_main


@dataclass
class CameraJob:
    camera: str           # DB에 들어갈 camera_model 값
    query: str            # 유튜브 검색어
    max_videos: int = 3   # 검색해서 처리할 최대 비디오 수
    comments_per_video: int = 40  # 비디오당 최대 댓글 수


# 🔧 여기만 수정해서 사용자가 원하는 카메라 목록 관리
CAMERA_JOBS: List[CameraJob] = [
    CameraJob(
        camera="Canon EOS R8",
        query="캐논 EOS R8 리뷰"
    ),
    CameraJob(
        camera="Canon EOS R6 Mark II",
        query="캐논 R6 마크2 리뷰"
    ),
    CameraJob(
        camera="Sony A7 IV",
        query="소니 A7M4 리뷰"
    ),
    # 👉 새로운 기종을 추가하고 싶으면 아래처럼 한 줄 더 추가하면 됩니다.
    # CameraJob(camera="Fujifilm X-S20", query="후지 X-S20 리뷰"),
]


def run_batch():
    print("📸 배치 크롤링 시작")
    print(f"총 대상 카메라 기종 수: {len(CAMERA_JOBS)}")
    print("-" * 60)

    for job in CAMERA_JOBS:
        print(f"\n🚀 크롤링 시작: {job.camera}")
        print(f"   검색어: {job.query}")
        print(f"   max_videos={job.max_videos}, comments_per_video={job.comments_per_video}")

        # crawl_youtube_comments.main 이 argparse.Namespace 비슷한걸 기대하므로,
        # 동일한 속성을 가진 간단한 객체를 만들어 전달
        class Args:
            pass

        args = Args()
        args.query = job.query
        args.camera = job.camera
        args.max_videos = job.max_videos
        args.comments_per_video = job.comments_per_video

        # 실제 크롤링 실행
        try:
            crawl_main(args)
        except Exception as e:
            print(f"❌ {job.camera} 크롤링 중 오류 발생:", e)
        else:
            print(f"✅ {job.camera} 크롤링 완료")

    print("\n🎉 모든 CameraJob 처리 완료")


if __name__ == "__main__":
    run_batch()