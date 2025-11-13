"""
datapipe/full_pipeline.py

원클릭 파이프라인:

  1) batch_crawl_cameras.py 를 이용해 여러 카메라 기종 댓글 크롤링
  2) label_with_model.py 를 이용해 새 리뷰 감성 라벨링
  3) DB 요약 통계(전체/기종별 개수, 감성 분포)를 간단히 출력

사용 방법:

  cd datapipe
  source .venv/bin/activate
  python full_pipeline.py

사전 준비:

  - YOUTUBE_API_KEY 환경 변수 설정
  - DATABASE_URL (선택, 없으면 기본값 postgresql+psycopg2://devuser:devpass@localhost:5432/camera_reviews)
  - PostgreSQL review 테이블 / 트리거 (reject_null_reviews) 등은 기존과 동일하게 세팅되었다고 가정
"""

import os
import sys
import subprocess

from pathlib import Path
from sqlalchemy import create_engine, text
from batch_crawl_cameras import run_batch  # 배치 크롤러


def run_labeling():
    """
    label_with_model.py 를 '스크립트'처럼 직접 실행해서 감성 라벨링 수행.

    → 터미널에서
       python label_with_model.py
    를 실행하는 것과 동일한 효과.
    """
    print("\n🧠 감성 라벨링 시작 (python label_with_model.py)")

    here = Path(__file__).resolve().parent   # datapipe 폴더
    script = here / "label_with_model.py"

    # 현재 사용 중인 파이썬 인터프리터로 label_with_model.py 실행
    subprocess.run([sys.executable, str(script)], check=True)

    print("🧠 감성 라벨링 완료\n")


def print_db_summary():
    """
    리뷰 DB 간단 요약 통계 출력:
      - 전체 리뷰 수
      - 카메라 기종별 개수
      - 감성 라벨별 개수
    """
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://devuser:devpass@localhost:5432/camera_reviews"
    )
    engine = create_engine(db_url, future=True)

    print("📊 DB 요약 통계")

    with engine.connect() as conn:
        # 전체 리뷰 수
        total = conn.execute(text("SELECT count(*) FROM review")).scalar_one()
        print(f"  • 전체 리뷰 수: {total}")

        # 카메라 기종별 개수
        print("  • 카메라 기종별 개수:")
        rows = conn.execute(text("""
            SELECT camera_model, count(*) AS cnt
            FROM review
            GROUP BY camera_model
            ORDER BY cnt DESC, camera_model
        """)).fetchall()
        for r in rows:
            cam = r[0] or "(NULL)"
            cnt = r[1]
            print(f"      - {cam}: {cnt}")

        # 감성 라벨별 개수
        print("  • 감성 라벨별 개수:")
        rows2 = conn.execute(text("""
            SELECT sentiment_label, count(*) AS cnt
            FROM review
            GROUP BY sentiment_label
            ORDER BY cnt DESC, sentiment_label
        """)).fetchall()
        for r in rows2:
            label = r[0] or "(NULL)"
            cnt = r[1]
            print(f"      - {label}: {cnt}")

    print("📊 요약 통계 출력 완료\n")


def main():
    print("===============================================")
    print("🚀 FULL PIPELINE START")
    print("   1) 배치 크롤링 (여러 카메라 기종)")
    print("   2) 감성 라벨링")
    print("   3) DB 요약 통계 출력")
    print("===============================================\n")

    # 1) 여러 카메라 기종 크롤링
    run_batch()

    # 2) 감성 라벨링
    run_labeling()

    # 3) 요약 통계 출력
    print_db_summary()

    print("✅ FULL PIPELINE DONE")


if __name__ == "__main__":
    main()