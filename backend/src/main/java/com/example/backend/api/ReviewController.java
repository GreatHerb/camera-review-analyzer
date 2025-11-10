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

    // 헬스체크
    @GetMapping("/health")
    public String health() { return "OK"; }

    // 최근 리뷰 20개
    @GetMapping("/reviews")
    public List<Review> reviews() {
        return reviewRepo.findTop20ByOrderByCreatedAtDesc();
    }

    // 요약 통계
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
}