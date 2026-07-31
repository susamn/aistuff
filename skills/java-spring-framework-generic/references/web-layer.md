# Spring: Web Layer

Sections 4-5: REST controllers and the service layer. Load when building or
reviewing request handling and business logic.

### 4. REST Controllers

#### Design Rules
- Controllers are **thin HTTP boundaries** only — no business logic, no repository calls.
- Use `@RestController` + `@RequestMapping` at the class level; map HTTP verbs with `@GetMapping`, `@PostMapping`, etc.
- Return `ResponseEntity<T>` only when you need to control the HTTP status or headers dynamically. For fixed-status endpoints, return the DTO directly and use `@ResponseStatus` on the method.

```java
@RestController
@RequestMapping("/api/v1/orders")
@RequiredArgsConstructor
@Tag(name = "Orders", description = "Order lifecycle management")
public class OrderController {

    private final OrderService orderService;

    @GetMapping("/{id}")
    @Operation(summary = "Fetch an order by ID")
    public OrderResponse getOrder(@PathVariable UUID id) {
        return orderService.findById(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public OrderResponse createOrder(@RequestBody @Valid CreateOrderRequest request) {
        return orderService.create(request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void cancelOrder(@PathVariable UUID id) {
        orderService.cancel(id);
    }
}
```

#### DTOs as Records
```java
// Request DTO — validated at the controller boundary
public record CreateOrderRequest(
    @NotNull UUID customerId,
    @NotEmpty List<@Valid OrderLineItem> items,
    @NotBlank String shippingAddress
) {}

// Response DTO — never expose entity fields directly
public record OrderResponse(
    UUID id,
    String status,
    BigDecimal totalAmount,
    Instant createdAt
) {}
```
- Use Java records for DTOs — they are immutable, compact, and generate `equals`/`hashCode`/`toString` automatically.
- Use a dedicated mapper (MapStruct recommended) to convert between entities and DTOs. Never do it inline in controllers or services.

#### API Versioning
- Version via URL path (`/api/v1/...`) for simplicity; use headers only when clients cannot change URLs.
- Never version by removing old endpoints — deprecate with `@Deprecated` + a `Deprecation` header, then remove after a defined sunset period.

---

### 5. Service Layer

- Every public method that writes state must be annotated `@Transactional`.
- Read-only methods should use `@Transactional(readOnly = true)` — Hibernate uses this to skip dirty-checking and flush, which improves read performance.
- **Never call a `@Transactional` method from within the same bean** (self-invocation bypasses the proxy and the transaction boundary). Extract to a separate bean if needed.
- Services must not import `jakarta.servlet.*` or any HTTP-layer type — they must remain transport-agnostic.

```java
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)   // default to read-only; override on writes
public class OrderService {

    private final OrderRepository orderRepository;
    private final OrderMapper orderMapper;
    private final ApplicationEventPublisher eventPublisher;

    public OrderResponse findById(UUID id) {
        return orderRepository.findById(id)
            .map(orderMapper::toResponse)
            .orElseThrow(() -> new NotFoundException("Order not found: " + id));
    }

    @Transactional
    public OrderResponse create(CreateOrderRequest request) {
        Order order = orderMapper.toEntity(request);
        Order saved = orderRepository.save(order);
        eventPublisher.publishEvent(new OrderCreatedEvent(saved.getId()));
        return orderMapper.toResponse(saved);
    }
}
```

---

