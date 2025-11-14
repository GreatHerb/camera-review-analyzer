"""
datapipe/batch_crawl_cameras.py

camera_list.json 파일에 정의된 여러 카메라 기종에 대해
한 번에 크롤링할 수 있는 스크립트.

사용 방법:

  cd datapipe
  source .venv/bin/activate
  python batch_crawl_cameras.py

사전 준비:
  - YOUTUBE_API_KEY 환경변수 설정 필요
  - crawl_youtube_comments.py 에서 DB 연결/트리거 등은 이미 세팅되어 있다고 가정
  - datapipe/camera_list.json 파일 형식 예:

    {
      "cameras": [
        {
          "camera": "Canon EOS R6 Mark II",
          "query": "캐논 R6 마크2 리뷰",
          "max_videos": 3,
          "comments_per_video": 40
        },
        {
          "camera": "Sony A7 IV",
          "query": "소니 A7M4 리뷰"
        }
      ]
    }

    → max_videos / comments_per_video 가 없으면 기본값 3 / 40 사용
"""

from dataclasses import dataclass
from typing import List
from pathlib import Path
import json

# 기존 크롤러의 main 함수를 재사용
from crawl_youtube_comments import main as crawl_main


@dataclass
class CameraJob:
    camera: str           # DB에 들어갈 camera_model 값
    query: str            # 유튜브 검색어
    max_videos: int = 3   # 검색해서 처리할 최대 비디오 수
    comments_per_video: int = 40  # 비디오당 최대 댓글 수


def load_camera_jobs() -> List[CameraJob]:
    """
    datapipe/camera_list.json 에서 카메라 목록을 읽어와 CameraJob 리스트로 변환.
    """
    path = Path(__file__).resolve().parent / "camera_list.json"
    if not path.exists():
        raise FileNotFoundError(
            f"camera_list.json 파일을 찾을 수 없습니다: {path}\n"
            f"예시 형식은 batch_crawl_cameras.py 상단 주석을 참고하세요."
        )

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    raw_list = data.get("cameras", [])
    jobs: List[CameraJob] = []

    for item in raw_list:
        camera = item.get("camera")
        query = item.get("query")
        if not camera or not query:
            # 최소 camera, query 는 있어야 의미가 있으니 스킵
            print(f"[warn] camera/query 둘 다 있어야 합니다. 스킵: {item}")
            continue

        max_videos = int(item.get("max_videos", 3))
        comments_per_video = int(item.get("comments_per_video", 40))

        jobs.append(
            CameraJob(
                camera=camera,
                query=query,
                max_videos=max_videos,
                comments_per_video=comments_per_video,
            )
        )

    return jobs


def run_batch():
    # JSON 에서 카메라 목록 불러오기
    camera_jobs = load_camera_jobs()

    print("📸 배치 크롤링 시작")
    print(f"총 대상 카메라 기종 수: {len(camera_jobs)}")
    print("-" * 60)

    for job in camera_jobs:
        print(f"\n🚀 크롤링 시작: {job.camera}")
        print(f"   검색어: {job.query}")
        print(f"   max_videos={job.max_videos}, comments_per_video={job.comments_per_video}")

        # crawl_youtube_comments.main 이 argparse.Namespace와 비슷한 객체를 기대하므로,
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