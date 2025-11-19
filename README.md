# Camera Review Analyzer

유튜브 카메라 리뷰/댓글을 크롤링해서  
**감성 분석(긍정/부정/중립)** + **키워드 분석**을 수행하고,  
웹 대시보드에서 **카메라 기종별/브랜드별 인사이트**를 시각화하는 개인 프로젝트입니다.

> Spring Boot + PostgreSQL + Python 데이터 파이프라인 + Docker 전반을 연습하기 위한 프로젝트입니다.

---

## 1. 주요 기능

### 1) 유튜브 댓글 크롤링 (Python)
- 검색어(query) + 카메라 기종(camera_model)을 기반으로 유튜브 댓글 자동 수집
- 동일 댓글 방지를 위해  
  **`UNIQUE(source, content)`** 제약 조건 활용
- 카메라 목록은 `camera_list.json` 에 정의 → 여기에 추가만 하면 전체 파이프라인 자동 처리
- 크롤링 파라미터 조절 가능  
  - 비디오 최대 개수  
  - 댓글 최대 개수

---

### 2) 감성 분석 (Python)
- HuggingFace 한국어 감성 모델  
  **`WhitePeak/bert-base-cased-Korean-sentiment`** 사용
- 리뷰별 결과 저장
  - 감성 라벨: Positive / Neutral / Negative  
  - 감정 점수(0~1)  
  - 모델 이름 저장  
  - DB에 자동 반영

---

### 3) 키워드 분석 (Python)
- 형태소 분석 기반 토큰 추출
- **카메라 기종 + 감성 라벨별** 키워드 상위 N개 자동 저장
- 결과는 `review_keyword_stats` 테이블로 관리
- 대시보드에서 실시간 필터링 가능

---

### 상단 카드
- 총 리뷰 수
- 평균 감성 점수
- 감성 분포 도넛 차트

### 리뷰 테이블
- 감성 점수 / 라벨 / 내용 / 등록일
- 실시간 검색 / 필터 / 페이지네이션

### 카메라 감성 랭킹
- 평균 감성 점수 상위 Top 10 노출

---

## 5. 기술 스택

### Backend
- Java 21
- Spring Boot 3.x
- Spring Data JPA + Hibernate
- PostgreSQL
- Maven Wrapper 기반 빌드

### Data Pipeline
- Python 3.13
- YouTube Data API (google-api-python-client)
- SQLAlchemy + psycopg2
- HuggingFace Transformers
- 형태소 분석기(필요 시 교체 가능)

### Infra
- Docker
- Docker Compose

---

## 6. DB 테이블 구조

### **review - 원본 리뷰 + 감성 분석 결과**
| 컬럼명 | 타입 | 설명 |
|-------|------|------|
| id | SERIAL PK | auto increment |
| source | TEXT | youtube:{videoId} |
| rating | INTEGER NULL | 유튜브 평점(없으면 NULL) |
| content | TEXT | 댓글 내용 |
| created_at | TIMESTAMP | 댓글 생성일 |
| camera_model | TEXT | 카메라 기종명 |
| sentiment_label | TEXT | positive / negative / neutral |
| sentiment_score | FLOAT | 0~1 사이 감정 점수 |
| model_name | TEXT | 감성 분석 모델 이름 |

### 제약/인덱스
- PRIMARY KEY (id)
- UNIQUE (source, content)
  - 같은 영상에서 동일한 내용의 댓글은 한 번만 저장(중복 크롤링 방지)
- BEFORE INSERT 트리거 trg_reject_null
  - content 또는 camera_model이 비어 있으면 삽입 자체를 막음(데이터 품질 관리)
    
---

### **review_keyword_stats**
| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | SERIAL PK | auto increment |
| camera_model | TEXT | 카메라 기종명 |
| sentiment_label | TEXT | 감성 라벨 |
| keyword | TEXT | 추출된 단어 |
| freq | INT | 등장 빈도 |
| updated_at | TIMESTAMP | 업데이트 시간 |

### 인덱스
- idx_rks_cam_sent (camera_model, sentiment_label)
  - 카메라 + 감성으로 빠르게 조회
- idx_rks_keyword (keyword)
  - 특정 키워드 기준 탐색/분석을 고려
    
---

## 🐳 7. Docker 실행 방법

### 1) 프로젝트 클론
```bash
git clone https://github.com/GreatHerb/camera-review-analyzer.git
cd camera-review-analyzer
```

### 2) Docker (Backend + DB) 실행
```bash
docker compose up -d --build
```

### 3) 접속
```bash
http://localhost:8081
```

### 4) PostgreSQL 접속
```bash
docker compose exec db psql -U devuser -d camera_reviews
```
---
## 8. Python 파이프라인 실행
> 도커와 별개로 로컬에서 크롤링 + 감성분석 + 키워드 분석을 돌리고 싶을 때 실행

### 1) 가상환경 활성화
```bash
cd datapipe
source .venv/bin/activate
```

### 2) 환경변수 설정
```bash
export DATABASE_URL="postgresql+psycopg2://devuser:devpass@localhost:5432/camera_reviews"
export YOUTUBE_API_KEY="YOUR_API_KEY"
```

### 3) 전체 파이프라인 실행
```bash
python full_pipeline.py
```

---
## 라이선스
> 본 프로젝트는 개인 포트폴리오 용도로 제작되었으며 상업적 활용을 의도하지 않습니다.
