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

    // 간단 리스트 (Swagger 테스트용)
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

    // 📊 요약 통계 (총 개수 + 평균 감성 점수)
    //  - 항상 "전체 기준"과 "선택 카메라 기준"을 함께 내려준다.
    @GetMapping("/stats/summary")
    public Map<String, Object> summary(
            @RequestParam(name = "camera", required = false) String camera
    ) {
        String cam = (camera != null && !camera.isBlank()) ? camera : null;

        // 전체 기준 (camera null)
        Long totalCount = reviewRepo.countByCamera(null);
        Double totalAvg = reviewRepo.findAvgSentimentScoreByCamera(null);
        if (totalAvg == null) {
            totalAvg = 0.0;
        }

        // 선택 카메라 기준 (없으면 전체 기준과 동일)
        Long camCount;
        Double camAvg;
        if (cam == null) {
            camCount = totalCount;
            camAvg = totalAvg;
        } else {
            camCount = reviewRepo.countByCamera(cam);
            camAvg = reviewRepo.findAvgSentimentScoreByCamera(cam);
            if (camAvg == null) {
                camAvg = 0.0;
            }
        }

        Map<String, Object> resp = new HashMap<>();
        // 기존 필드(호환용): 선택 카메라 기준
        resp.put("count", camCount != null ? camCount : 0L);
        resp.put("avgSentiment", camAvg);

        // 새 필드: 전체 기준 정보
        resp.put("globalCount", totalCount != null ? totalCount : 0L);
        resp.put("globalAvgSentiment", totalAvg);

        // 어떤 카메라 기준인지 정보
        resp.put("camera", cam);

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

    // 카메라 기종 목록 반환 (드롭다운용)
    @GetMapping("/cameras")
    public List<String> cameras() {
        return reviewRepo.findDistinctCameraModels();
    }
    
    // 📈 카메라별 평균 감성 점수 랭킹
    @GetMapping("/stats/ranking")
    public List<Map<String, Object>> ranking(
            @RequestParam(name = "minCount", defaultValue = "30") int minCount
    ) {
        List<Object[]> rows = reviewRepo.findCameraRanking(minCount);
        List<Map<String, Object>> list = new java.util.ArrayList<>();

        for (Object[] row : rows) {
            String camera = (String) row[0];
            long cnt      = ((Number) row[1]).longValue();
            double avg    = ((Number) row[2]).doubleValue();

            Map<String, Object> m = new HashMap<>();
            m.put("camera", camera);
            m.put("count", cnt);
            m.put("avgSentiment", avg);
            list.add(m);
        }

        return list;
    }
}