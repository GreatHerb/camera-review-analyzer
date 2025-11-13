package com.example.backend.api;

import com.example.backend.domain.Review;
import com.example.backend.repo.ReviewRepo;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class ReviewController {

    private final ReviewRepo reviewRepo;

    public ReviewController(ReviewRepo reviewRepo) {
        this.reviewRepo = reviewRepo;
    }

    // 헬스 체크
    @GetMapping("/health")
    public Map<String, String> health() {
        Map<String, String> m = new HashMap<>();
        m.put("status", "OK");
        return m;
    }

    // 간단 리스트 (대시보드에서 안 쓰더라도 Swagger 테스트용으로 유지)
    @GetMapping("/reviews")
    public List<Review> latest(@RequestParam(required = false) String sentiment) {
        if (sentiment == null || sentiment.isBlank()) {
            return reviewRepo.findTop20ByOrderByCreatedAtDesc();
        }
        return reviewRepo.findTop20BySentimentLabelOrderByCreatedAtDesc(sentiment);
    }

    // 🔍 검색 + 페이지네이션 + 감성/카메라/키워드 필터
    @GetMapping("/reviews/search")
    public Page<Review> search(
            @RequestParam(required = false) String sentiment,
            @RequestParam(required = false) String camera,
            @RequestParam(required = false) String query,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        Pageable pageable = PageRequest.of(page, size);
        return reviewRepo.search(sentiment, camera, query, pageable);
    }

    // 📊 요약 통계 (총 개수 + 평균 감성 점수) - 카메라 선택에 따라 달라짐
    @GetMapping("/stats/summary")
    public Map<String, Object> summary(
            @RequestParam(name = "camera", required = false) String camera
    ) {
        Long count = reviewRepo.countByCamera(camera);
        Double avg = reviewRepo.findAvgSentimentScoreByCamera(camera);
        if (avg == null) {
            avg = 0.0;
        }

        Map<String, Object> resp = new HashMap<>();
        resp.put("count", count != null ? count : 0L);
        resp.put("avgSentiment", avg);
        return resp;
    }

    // 📊 감성 분포 (positive/neutral/negative 개수) - 카메라별 필터 가능
    @GetMapping("/stats/sentiment")
    public Map<String, Object> sentimentStats(
            @RequestParam(name = "camera", required = false) String camera
    ) {
        List<Object[]> rows = reviewRepo.countBySentimentGroup(camera);
        Map<String, Long> buckets = new HashMap<>();
        long total = 0L;

        for (Object[] row : rows) {
            String label = (String) row[0];
            long cnt = ((Number) row[1]).longValue();
            buckets.put(label, cnt);
            total += cnt;
        }

        Map<String, Object> resp = new HashMap<>();
        resp.put("total", total);
        resp.put("buckets", buckets);
        return resp;
    }

    // 📷 카메라 기종 목록 (드롭다운용)
    @GetMapping("/cameras")
    public List<String> cameras() {
        return reviewRepo.findDistinctCameraModels();
    }
}