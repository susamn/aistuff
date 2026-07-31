# Spring: Operations

Sections 11-14: observability, async and concurrency, domain events, caching.
Load for runtime behaviour and production concerns.

### 11. Observability

#### Spring Boot Actuator
```yaml
management:
  endpoints:
    web:
      exposure:
        include: health, info, metrics, prometheus
  endpoint:
    health:
      show-details: when-authorized
      probes:
        enabled: true          # enables /health/liveness and /health/readiness for K8s
  metrics:
    tags:
      application: ${spring.application.name}
```
- **Never expose all actuator endpoints publicly** — secure them behind a role or restrict to an internal management port.
- Use `/health/liveness` and `/health/readiness` as Kubernetes probe targets.

#### Micrometer Metrics
```java
@Service
@RequiredArgsConstructor
public class OrderService {

    private final MeterRegistry registry;

    @Counted(value = "orders.created", description = "Total orders created")
    @Timed(value = "orders.create.duration", description = "Time to create an order")
    @Transactional
    public OrderResponse create(CreateOrderRequest request) { ... }
}
```
- Tag metrics with `application`, `environment`, and relevant business dimensions (e.g., `order.type`).
- Export to **Prometheus** via `micrometer-registry-prometheus`; visualize with Grafana.

#### Distributed Tracing
- Use **Micrometer Tracing** with the OpenTelemetry bridge (`micrometer-tracing-bridge-otel`) — the replacement for Spring Cloud Sleuth in Spring Boot 3.x.
- Propagate `traceId` and `spanId` in log output via MDC (Logback auto-configures this when `micrometer-tracing` is on the classpath).
- Include `traceId` in API error responses to correlate user-reported errors with logs.

---

### 12. Async & Concurrency

#### Virtual Threads (Java 21 + Spring Boot 3.2+)
```yaml
# Enable virtual threads for embedded Tomcat — replaces the platform thread pool
spring:
  threads:
    virtual:
      enabled: true
```
- With virtual threads enabled, you can use blocking I/O in `@Async` methods and request handlers without thread-pool starvation — the JVM handles the scheduling.
- **Do not use `synchronized` blocks with virtual threads** — use `ReentrantLock` or `java.util.concurrent` primitives instead (synchronized pins carrier threads).

#### `@Async` for Fire-and-Forget
```java
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean(name = "taskExecutor")
    public Executor taskExecutor() {
        // With virtual threads enabled, this delegates to virtual thread factory
        return Executors.newVirtualThreadPerTaskExecutor();
    }
}

@Service
public class NotificationService {

    @Async("taskExecutor")
    public CompletableFuture<Void> sendWelcomeEmail(String email) {
        // I/O-bound work — perfect for virtual threads
        return CompletableFuture.completedFuture(null);
    }
}
```
- Always return `CompletableFuture<T>` from `@Async` methods — it allows callers to await completion and handle exceptions.
- Configure a custom executor with a meaningful name, rejection policy, and queue capacity.

---

### 13. Domain Events

- Use **`ApplicationEventPublisher`** to decouple domain side-effects (sending emails, updating read models, triggering workflows) from the core write transaction.
- Use `@TransactionalEventListener(phase = AFTER_COMMIT)` for listeners that must run only after the DB transaction commits successfully:

```java
// Publishing (in service)
eventPublisher.publishEvent(new OrderShippedEvent(order.getId(), order.getCustomerId()));

// Listening (in a separate bean)
@Component
@Slf4j
@RequiredArgsConstructor
public class OrderNotificationListener {

    private final NotificationService notificationService;

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    @Async
    public void onOrderShipped(OrderShippedEvent event) {
        notificationService.sendShippingConfirmation(event.customerId());
    }
}
```
- Keep event payloads as **immutable records** containing only IDs and essential data — never full entities.
- For cross-service event propagation, prefer a message broker (Kafka, RabbitMQ via Spring Cloud Stream) over in-process events.

---

### 14. Caching

```java
@Configuration
@EnableCaching
public class CacheConfig {

    @Bean
    public CacheManager cacheManager() {
        // Use Caffeine for in-process; swap to Redis for distributed
        CaffeineCacheManager manager = new CaffeineCacheManager();
        manager.setCaffeine(Caffeine.newBuilder().expireAfterWrite(10, TimeUnit.MINUTES).maximumSize(500));
        return manager;
    }
}

@Service
public class ProductService {

    @Cacheable(value = "products", key = "#id", unless = "#result == null")
    public ProductResponse findById(UUID id) { ... }

    @CacheEvict(value = "products", key = "#id")
    @Transactional
    public ProductResponse update(UUID id, UpdateProductRequest req) { ... }

    @CacheEvict(value = "products", allEntries = true)
    @Scheduled(cron = "0 0 * * * *")   // full eviction hourly as a safety net
    public void evictAllProducts() {}
}
```
- **Never cache mutable state that must be immediately consistent** — only cache reference data, read-heavy aggregates, or expensive computations.
- Always set a TTL and maximum size; unbounded caches are memory leaks.
- Use **Redis** (via `spring-boot-starter-data-redis`) for distributed / multi-instance deployments.

---

