package com.example.backend.api;

import com.example.backend.domain.Review;
import com.example.backend.repo.ReviewRepo;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public class ReviewController {

    private final ReviewRepo reviewRepo;

    public ReviewController(ReviewRepo reviewRepo) {
        this.reviewRepo = reviewRepo;
    }

    // 헬스체크
    @GetMapping("/health")
    public String health() {
        return "OK";
    }

    // 대시보드용: 최신 20개 (감성 필터 옵션)
    // ※ 기존 프런트(index.html)가 이 엔드포인트를 사용하므로 형태 유지
    @GetMapping("/reviews")
    public List<Review> reviews(@RequestParam(required = false) String sentiment) {
        if (sentiment == null || sentiment.isBlank()) {
            return reviewRepo.findTop20ByOrderByCreatedAtDesc();
        } else {
            return reviewRepo.findTop20BySentimentLabelOrderByCreatedAtDesc(sentiment);
        }
    }

    // 신규: 페이지네이션 + 검색 + 감성 필터 (정렬은 JPQL에서 최신순 고정)
    @GetMapping("/reviews/search")
    public Map<String, Object> search(
            @RequestParam(required = false) String sentiment,
            @RequestParam(required = false) String query,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size
    ) {
        var pageable = org.springframework.data.domain.PageRequest.of(page, size);
        var resultPage = reviewRepo.findFiltered(
                (sentiment == null || sentiment.isBlank()) ? null : sentiment,
                (query == null || query.isBlank()) ? null : query,
                pageable
        );

        Map<String, Object> out = new HashMap<>();
        out.put("content", resultPage.getContent());
        out.put("page", resultPage.getNumber());
        out.put("size", resultPage.getSize());
        out.put("totalPages", resultPage.getTotalPages());
        out.put("totalElements", resultPage.getTotalElements());
        return out;
    }

    // 감성 통계 (차트용)
    @GetMapping("/stats/sentiment")
    public Map<String, Object> sentimentStats() {
        List<Object[]> rows = reviewRepo.countBySentimentGroup();
        Map<String, Long> buckets = new HashMap<>();
        long total = 0L;

        for (Object[] r : rows) {
            String label = (String) r[0];
            Long cnt = (Long) r[1];
            buckets.put(label == null ? "unknown" : label, cnt);
            total += cnt;
        }

        Map<String, Object> out = new HashMap<>();
        out.put("total", total);
        out.put("buckets", buckets);
        return out;
    }

    // 요약 통계 (개수/평균 평점)
    @GetMapping("/stats/summary")
    public Map<String, Object> summary() {
        List<Review> all = reviewRepo.findAll();
        int count = all.size();
        double avg = 0.0;
        if (count > 0) {
            avg = all.stream()
                     .filter(r -> r.getRating() != null)
                     .collect(Collectors.averagingDouble(r -> r.getRating()))
                     .doubleValue();
        }
        Map<String, Object> out = new HashMap<>();
        out.put("count", count);
        out.put("avgRating", avg);
        return out;
    }
}