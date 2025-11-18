# -------- 1단계: 빌드용 이미지 (Maven + JDK) --------
FROM eclipse-temurin:21-jdk-jammy AS builder

WORKDIR /app

# Maven Wrapper & 설정 먼저 복사 (의존성 캐시 최적화)
COPY mvnw ./
COPY .mvn .mvn
COPY pom.xml ./

# 의존성 미리 내려받기
RUN ./mvnw -q -B -DskipTests dependency:go-offline

# 실제 소스 복사 후 빌드
COPY src ./src
RUN ./mvnw -q -B -DskipTests package

# -------- 2단계: 실행용 이미지 (JRE만) --------
FROM eclipse-temurin:21-jre-jammy

WORKDIR /app

# 위에서 빌드한 JAR 복사 (이름은 pom.xml의 artifactId/버전 기준)
COPY --from=builder /app/target/backend-0.0.1-SNAPSHOT.jar app.jar

# 컨테이너 내부에서 사용할 포트 (application.properties의 server.port=8081 기준)
EXPOSE 8081

# 스프링 부트 앱 실행
ENTRYPOINT ["java", "-jar", "/app/app.jar"]