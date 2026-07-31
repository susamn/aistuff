# Spring: Foundations

Sections 0-3: version baseline, project bootstrap and structure, dependency
injection, configuration management. Load when starting or restructuring an app.

### 0. Version Baseline

- **Spring Boot 3.x** (minimum 3.2) with **Java 21 LTS** is the target baseline.
- Spring Boot 3.x requires **Jakarta EE 10** — all `javax.*` imports become `jakarta.*` (persistence, validation, servlet, etc.). Never mix the two.
- Use the **Spring Boot BOM** as the dependency version anchor; override individual versions only when a CVE or feature specifically requires it.
- Track the [Spring Boot support timeline](https://spring.io/projects/spring-boot#support); run on a supported OSS or commercial release only.

---

### 1. Project Bootstrap & Structure

#### Starting a Project
- Use [start.spring.io](https://start.spring.io) (or the IntelliJ / VS Code Spring Initializr plugin) for new projects. Do not assemble BOMs manually.
- **Contract First:** Always check if there is an existing OpenAPI schema available. If yes, build the API around it. If starting from scratch, always design and provide an OpenAPI schema for the APIs first.
- Select dependencies deliberately — avoid pulling in starters you won't use (they add auto-configuration and startup overhead).

#### Recommended Starter Set (web API)
```
spring-boot-starter-web          # MVC + embedded Tomcat (or swap to WebFlux)
spring-boot-starter-data-jpa     # Hibernate + Spring Data
spring-boot-starter-validation   # Jakarta Bean Validation
spring-boot-starter-security     # Spring Security
spring-boot-starter-actuator     # Health, metrics, info endpoints
spring-boot-starter-test         # JUnit 5, Mockito, AssertJ, MockMvc
springdoc-openapi-starter-webmvc-ui  # OpenAPI 3 + Swagger UI
```

#### Package Layout
```
src/
  main/
    java/com/example/app/
      Application.java              ← @SpringBootApplication (root package only)
      controller/                   ← @RestController, thin HTTP boundary
      service/                      ← @Service, business logic
      repository/                   ← @Repository, Spring Data interfaces
      domain/                       ← JPA @Entity classes, domain model
      dto/                          ← Request/Response records and classes
      config/                       ← @Configuration classes, Beans
      exception/                    ← Custom exception hierarchy
      security/                     ← Security config, filters, handlers
      event/                        ← Domain events and listeners
    resources/
      application.yml               ← Base config
      application-local.yml         ← Local dev overrides (gitignored)
      application-test.yml          ← Test overrides
  test/
    java/com/example/app/
      controller/                   ← @WebMvcTest slice tests
      service/                      ← Unit tests with Mockito
      repository/                   ← @DataJpaTest slice tests
      integration/                  ← @SpringBootTest + Testcontainers
```

- **`Application.java` must live in the root package** so component scanning covers all sub-packages without explicit `scanBasePackages`.
- Keep `config/` classes focused: one `@Configuration` per concern (security, cache, async, openapi, etc.). Never mix unrelated beans in a single config class.

---

### 2. Dependency Injection

#### Constructor Injection (Always)
```java
// ✅ Correct — Lombok @RequiredArgsConstructor generates the constructor
@Service
@RequiredArgsConstructor
public class OrderService {
    private final OrderRepository orderRepository;
    private final PaymentGateway paymentGateway;
    private final ApplicationEventPublisher eventPublisher;
}

// ❌ Never — field injection hides dependencies, breaks testability
@Service
public class OrderService {
    @Autowired private OrderRepository orderRepository;
}
```
- Mark injected fields `private final` — this enforces immutability and makes the dependency graph explicit.
- Use `@RequiredArgsConstructor` (Lombok) to eliminate boilerplate; only write the constructor manually when you need custom validation or logging inside it.

#### Bean Scoping
- Default to `@Scope("singleton")` (Spring's default) — never deviate without explicit justification.
- Use `@RequestScope` only for beans that truly carry per-request state (e.g., a security context holder wrapper).
- Avoid prototype-scoped beans injected into singletons without a `Provider<T>` or `ObjectFactory<T>` wrapper — it causes stale-proxy bugs.

---

### 3. Configuration Management

#### `application.yml` over `application.properties`
- Prefer YAML for hierarchy and readability; keep the base file for shared config and use profile-specific files for overrides.

#### Typed Configuration with `@ConfigurationProperties`
```java
// ✅ Bind a whole config namespace to a strongly-typed bean
@ConfigurationProperties(prefix = "app.payment")
@Validated
public record PaymentProperties(
    @NotBlank String gatewayUrl,
    @NotBlank String apiKey,
    @Min(1) @Max(30) int timeoutSeconds
) {}

// Register it
@SpringBootApplication
@EnableConfigurationProperties(PaymentProperties.class)
public class Application { ... }
```
- **Never** use `@Value("${some.property}")` for groups of related properties — it scatters config across the codebase.
- Use `@Value` only for single, isolated values injected into a `@Bean` method in a `@Configuration` class.
- Keep secrets out of YAML entirely. Reference environment variables:
  ```yaml
  app:
    payment:
      api-key: ${PAYMENT_API_KEY}   # resolved from env at runtime
  ```

#### Profiles
- Define environments with profiles: `local`, `dev`, `staging`, `prod`.
- Activate via `SPRING_PROFILES_ACTIVE` environment variable, not in checked-in YAML.
- Use `application-local.yml` (gitignored) for developer-specific overrides (local DB URLs, stubbed services).
- Never use `@Profile` on `@Service` or `@Repository` beans — it makes the business logic depend on infrastructure decisions. Use it only in `@Configuration` classes to swap implementations.

---

