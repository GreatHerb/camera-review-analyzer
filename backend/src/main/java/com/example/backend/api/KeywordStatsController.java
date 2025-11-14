package com.example.backend.api;

//import com.example.backend.domain.ReviewKeywordStat;
import com.example.backend.repo.ReviewKeywordStatRepo;
import org.springframework.data.domain.PageRequest;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/stats")
public class KeywordStatsController {

    private final ReviewKeywordStatRepo keywordRepo;

    public KeywordStatsController(ReviewKeywordStatRepo keywordRepo) {
        this.keywordRepo = keywordRepo;
    }

    public record KeywordDto(
            String cameraModel,
            String sentimentLabel,
            String keyword,
            int freq
    ) {}

    @GetMapping("/keywords")
    public List<KeywordDto> keywords(
            @RequestParam(required = false) String camera,
            @RequestParam(required = false) String sentiment,
            @RequestParam(defaultValue = "20") int limit
    ) {
        int size = Math.max(1, Math.min(limit, 100));

        String cameraFilter = normalize(camera);
        String sentimentFilter = normalize(sentiment);

        var page = keywordRepo.findByFilters(
                cameraFilter,
                sentimentFilter,
                PageRequest.of(0, size)
        );

        return page.getContent().stream()
                .map(k -> new KeywordDto(
                        k.getCameraModel(),
                        k.getSentimentLabel(),
                        k.getKeyword(),
                        k.getFreq() == null ? 0 : k.getFreq()
                ))
                .toList();
    }

    private String normalize(String v) {
        if (v == null) return null;
        String t = v.trim();
        if (t.isEmpty()) return null;
        if ("ALL".equalsIgnoreCase(t)) return null;   // "전체" 개념
        return t;
    }
}