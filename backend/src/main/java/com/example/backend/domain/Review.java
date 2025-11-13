package com.example.backend.domain;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "review")
public class Review {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String source;

    private Double rating;

    @Column(columnDefinition = "TEXT")
    private String content;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "sentiment_label")
    private String sentimentLabel;

    @Column(name = "sentiment_score")
    private Double sentimentScore;

    @Column(name = "sentiment_model")
    private String sentimentModel;

    @Column(name = "camera_model")
    private String cameraModel;

    public String getSentimentLabel() { return sentimentLabel; }
    public void setSentimentLabel(String s) { this.sentimentLabel = s; }

    public Double getSentimentScore() { return sentimentScore; }
    public void setSentimentScore(Double s) { this.sentimentScore = s; }

    public String getSentimentModel() { return sentimentModel; }
    public void setSentimentModel(String s) { this.sentimentModel = s; }
    
    public String getCameraModel() { return cameraModel; }
    public void setCameraModel(String cameraModel) { this.cameraModel = cameraModel; }
    
    // --- getters / setters (롬복 안 쓰는 버전) ---
    public Long getId() { return id; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public Double getRating() { return rating; }
    public void setRating(Double rating) { this.rating = rating; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}