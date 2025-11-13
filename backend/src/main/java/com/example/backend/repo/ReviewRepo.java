package com.example.backend.repo;

import com.example.backend.domain.Review;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface ReviewRepo extends JpaRepository<Review, Long> {

    // 최신 20개 (간단 리스트용)
    List<Review> findTop20ByOrderByCreatedAtDesc();

    // 감성 라벨로 필터 + 최신 20개
    List<Review> findTop20BySentimentLabelOrderByCreatedAtDesc(String sentimentLabel);

    // ====== 검색(페이지네이션) ======
    @Query("""
        SELECT r FROM Review r
        WHERE (:sentiment IS NULL OR :sentiment = '' OR r.sentimentLabel = :sentiment)
          AND (:camera   IS NULL OR :camera   = '' OR r.cameraModel    = :camera)
          AND (:query    IS NULL OR :query    = '' OR LOWER(r.content) LIKE LOWER(CONCAT('%', :query, '%')))
        ORDER BY r.createdAt DESC
    """)
    Page<Review> search(String sentiment, String camera, String query, Pageable pageable);

    // ====== 통계용: 전체/카메라별 감성 분포 ======
    @Query("""
        SELECT r.sentimentLabel AS label, COUNT(r) AS cnt
          FROM Review r
         WHERE (:camera IS NULL OR :camera = '' OR r.cameraModel = :camera)
         GROUP BY r.sentimentLabel
    """)
    List<Object[]> countBySentimentGroup(String camera);

    // ====== 통계용: 평균 감성 점수 (전체/카메라별) ======
    @Query("""
        SELECT COALESCE(AVG(r.sentimentScore), 0)
          FROM Review r
         WHERE (:camera IS NULL OR :camera = '' OR r.cameraModel = :camera)
    """)
    Double findAvgSentimentScoreByCamera(String camera);

    // ====== 통계용: 리뷰 개수 (전체/카메라별) ======
    @Query("""
        SELECT COUNT(r)
          FROM Review r
         WHERE (:camera IS NULL OR :camera = '' OR r.cameraModel = :camera)
    """)
    Long countByCamera(String camera);

    // ====== 드롭다운용: 카메라 기종 목록 ======
    @Query("""
        SELECT DISTINCT r.cameraModel
          FROM Review r
         WHERE r.cameraModel IS NOT NULL AND r.cameraModel <> ''
         ORDER BY r.cameraModel ASC
    """)
    List<String> findDistinctCameraModels();
}