# Spring: Api And Release

Sections 15-16: OpenAPI documentation and the production readiness checklist.
Load before shipping.

### 15. OpenAPI Documentation

```java
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI applicationOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("Order Service API")
                .version("v1")
                .description("Manages the full order lifecycle")
                .contact(new Contact().name("Platform Engineering").email("platform@example.com")))
            .addSecurityItem(new SecurityRequirement().addList("bearerAuth"))
            .components(new Components()
                .addSecuritySchemes("bearerAuth", new SecurityScheme()
                    .type(SecurityScheme.Type.HTTP).scheme("bearer").bearerFormat("JWT")));
    }
}
```
- Annotate controllers with `@Tag`, endpoints with `@Operation`, and response types with `@ApiResponse`.
- Keep Swagger UI disabled in production (`springdoc.swagger-ui.enabled=false` in the `prod` profile).
- Export the OpenAPI spec as a static file (`/v3/api-docs`) and version it alongside the codebase.

---

### 16. Production Readiness Checklist

```
□ Health probes configured (/health/liveness, /health/readiness)
□ Graceful shutdown enabled (server.shutdown=graceful)
□ Actuator secured — not exposed on public port
□ All secrets in environment variables or secrets manager (not in YAML)
□ Flyway / Liquibase migrations enabled; ddl-auto=validate or none
□ Connection pool sized (HikariCP: pool-size tuned per instance count)
□ Virtual threads enabled (spring.threads.virtual.enabled=true)
□ Distributed tracing configured (Micrometer Tracing + OTEL exporter)
□ Prometheus metrics endpoint exposed
□ Log format structured JSON (Logstash encoder or ECS layout for ELK)
□ OWASP Dependency-Check in CI pipeline
□ SpotBugs / ErrorProne in build
□ Testcontainers integration tests running in CI
□ Docker image built with layered JARs (spring-boot:build-image or Jib)
□ JVM flags set for container: -XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0
