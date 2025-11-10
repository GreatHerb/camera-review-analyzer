package com.example.backend.repo;

import com.example.backend.domain.Review;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface ReviewRepo extends JpaRepository<Review, Long> {

    // 최신 20개
    List<Review> findTop20ByOrderByCreatedAtDesc();

    // 감성 라벨로 필터 + 최신 20개
    List<Review> findTop20BySentimentLabelOrderByCreatedAtDesc(String sentimentLabel);

    // 페이지네이션 + 검색어 + 감성 필터 (검색 API용)
    @Query("""
        SELECT r FROM Review r
         WHERE (:sentiment IS NULL OR r.sentimentLabel = :sentiment)
           AND (:query IS NULL OR LOWER(r.content) LIKE LOWER(CONCAT('%', :query, '%')))
         ORDER BY r.createdAt DESC
    """)
    Page<Review> findFiltered(String sentiment, String query, Pageable pageable);

    // 감성 라벨별 개수 집계
    @Query("SELECT r.sentimentLabel AS label, COUNT(r) AS cnt FROM Review r GROUP BY r.sentimentLabel")
    List<Object[]> countBySentimentGroup();
}