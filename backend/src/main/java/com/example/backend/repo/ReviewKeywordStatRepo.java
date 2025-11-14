package com.example.backend.repo;

import com.example.backend.domain.ReviewKeywordStat;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.*;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface ReviewKeywordStatRepo extends JpaRepository<ReviewKeywordStat, Long> {

    @Query("""
        SELECT k FROM ReviewKeywordStat k
        WHERE (:camera IS NULL OR :camera = '' OR k.cameraModel = :camera)
          AND (:sentiment IS NULL OR :sentiment = '' OR k.sentimentLabel = :sentiment)
        ORDER BY k.freq DESC
        """)
    Page<ReviewKeywordStat> findByFilters(
            @Param("camera") String camera,
            @Param("sentiment") String sentiment,
            Pageable pageable
    );

    @Query("SELECT DISTINCT k.cameraModel FROM ReviewKeywordStat k ORDER BY k.cameraModel")
    List<String> findDistinctCameraModels();
}