# Spring: Data Access

Section 6: Spring Data JPA. Load when touching repositories, entities,
queries, or transactions.

### 6. Data Access — Spring Data JPA

#### Entity Design
```java
@Entity
@Table(name = "orders")
@Getter                          // Lombok — only getters; entities should not be fully mutable
@NoArgsConstructor(access = AccessLevel.PROTECTED)  // required by JPA
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)  // Java UUID, no sequence contention
    private UUID id;

    @Column(nullable = false)
    private UUID customerId;

    @Enumerated(EnumType.STRING)  // always STRING, never ORDINAL
    @Column(nullable = false)
    private OrderStatus status;

    @CreationTimestamp
    private Instant createdAt;

    @UpdateTimestamp
    private Instant updatedAt;

    @Version                      // optimistic locking — always include on mutable entities
    private Long version;

    // Factory method instead of public constructor
    public static Order create(UUID customerId) {
        Order o = new Order();
        o.customerId = customerId;
        o.status = OrderStatus.PENDING;
        return o;
    }
}
```

#### Repository Patterns
```java
public interface OrderRepository extends JpaRepository<Order, UUID> {

    // Derived query — fine for simple predicates
    List<Order> findByCustomerIdAndStatus(UUID customerId, OrderStatus status);

    // JPQL for complex queries — prefer over native SQL for portability
    @Query("SELECT o FROM Order o WHERE o.createdAt >= :since AND o.status = :status")
    Page<Order> findRecentByStatus(@Param("since") Instant since,
                                   @Param("status") OrderStatus status,
                                   Pageable pageable);

    // Projection — avoid SELECT * when only a subset of fields is needed
    @Query("SELECT o.id as id, o.status as status FROM Order o WHERE o.customerId = :id")
    List<OrderSummary> findSummariesByCustomerId(@Param("id") UUID customerId);
}
```

#### JPA Rules
- **Always use `EnumType.STRING`** — `ORDINAL` breaks if the enum order ever changes.
- **Always add `@Version`** on entities with concurrent writes for optimistic locking.
- **Avoid `FetchType.EAGER`** — it generates N+1 queries. Use `FetchType.LAZY` everywhere and load associations explicitly with `JOIN FETCH` in JPQL when needed.
- **Use Projections** (interfaces or records) for read-heavy queries to avoid hydrating full entity objects.
- **Never call `flush()` or `clear()` manually** outside of batch-processing loops — it defeats JPA's unit-of-work semantics.
- Use **Flyway** or **Liquibase** for schema migrations. Never rely on `spring.jpa.hibernate.ddl-auto=update` in any environment above `local`.

---

