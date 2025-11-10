package com.example.backend.repo;

import com.example.backend.domain.Review;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface ReviewRepo extends JpaRepository<Review, Long> {

    // 최신 20개
    List<Review> findTop20ByOrderByCreatedAtDesc();

    // 감성 라벨로 필터 + 최신 20개
    List<Review> findTop20BySentimentLabelOrderByCreatedAtDesc(String sentimentLabel);

    // 감성 라벨별 개수 집계
    @Query("select r.sentimentLabel as label, count(r) as cnt from Review r group by r.sentimentLabel")
    List<Object[]> countBySentimentGroup();
}