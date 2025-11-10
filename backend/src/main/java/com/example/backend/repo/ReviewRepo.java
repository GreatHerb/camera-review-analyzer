package com.example.backend.repo;

import com.example.backend.domain.Review;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ReviewRepo extends JpaRepository<Review, Long> {
    List<Review> findTop20ByOrderByCreatedAtDesc();
}