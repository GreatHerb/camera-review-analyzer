package com.example.backend.api;

import com.example.backend.domain.Review;
import com.example.backend.repo.ReviewRepo;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api")
public class ReviewController {

    private final ReviewRepo reviewRepo;

    public ReviewController(ReviewRepo reviewRepo) {
        this.reviewRepo = reviewRepo;
    }

    @GetMapping("/health")
    public String health() {
        return "OK";
    }

    // ✅ 단일 메서드로 통합: sentiment 파라미터는 선택 사항
    @GetMapping("/reviews")
    public List<Review> reviews(@RequestParam(name = "sentiment", required = false) String sentiment) {
        if (sentiment == null || sentiment.isBlank()) {
            return reviewRepo.findTop20ByOrderByCreatedAtDesc();
        }
        return reviewRepo.findTop20BySentimentLabelOrderByCreatedAtDesc(sentiment);
    }

    @GetMapping("/stats/summary")
    public Map<String, Object> summary() {
        var list = reviewRepo.findAll();
        double avg = list.stream()
                .map(r -> r.getRating() == null ? 0.0 : r.getRating())
                .mapToDouble(Double::doubleValue)
                .average()
                .orElse(0.0);
        Map<String, Object> m = new HashMap<>();
        m.put("count", list.size());
        m.put("avgRating", Math.round(avg * 100.0) / 100.0);
        return m;
    }

    @GetMapping("/stats/sentiment")
    public Map<String, Object> sentimentStats() {
        var rows = reviewRepo.countBySentimentGroup();
        Map<String, Long> buckets = new HashMap<>();
        long total = 0L;
        for (Object[] row : rows) {
            String label = (String) row[0];
            Long cnt = ((Number) row[1]).longValue();
            buckets.put(label == null ? "unknown" : label, cnt);
            total += cnt;
        }
        Map<String, Object> out = new HashMap<>();
        out.put("total", total);
        out.put("buckets", buckets);
        return out;
    }
}