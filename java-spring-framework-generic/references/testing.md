# Spring: Testing

Section 10: testing strategy. Load when writing or reviewing tests.

### 10. Testing Strategy

#### Test Pyramid
```
                      ┌────────────────────────┐
                      │   @SpringBootTest       │  ← Integration / E2E (few, slow)
                      │   + Testcontainers      │
                  ┌───┴────────────────────────┴───┐
                  │  @WebMvcTest   @DataJpaTest     │  ← Slice tests (medium)
              ┌───┴─────────────────────────────────┴───┐
              │        Plain JUnit 5 + Mockito           │  ← Unit tests (many, fast)
              └─────────────────────────────────────────┘
```

#### Unit Tests (Service Layer)
```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock OrderRepository orderRepository;
    @Mock OrderMapper orderMapper;
    @Mock ApplicationEventPublisher eventPublisher;

    @InjectMocks OrderService orderService;

    @Test
    void should_throwNotFoundException_when_orderIdDoesNotExist() {
        given(orderRepository.findById(any())).willReturn(Optional.empty());
        assertThatThrownBy(() -> orderService.findById(UUID.randomUUID()))
            .isInstanceOf(NotFoundException.class);
    }
}
```

#### Slice Tests — Controller (`@WebMvcTest`)
- **Always use MockMvc** for testing REST controllers to verify HTTP mappings, validation, and JSON serialization.

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired MockMvc mockMvc;
    @MockBean OrderService orderService;
    @Autowired ObjectMapper objectMapper;

    @Test
    void should_return404_when_orderNotFound() throws Exception {
        given(orderService.findById(any())).willThrow(new NotFoundException("Order not found"));
        mockMvc.perform(get("/api/v1/orders/{id}", UUID.randomUUID()))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.status").value(404));
    }
}
```

#### Slice Tests — Repository (`@DataJpaTest`)
```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = NONE)   // use real DB via Testcontainers
@Import(TestcontainersConfig.class)
class OrderRepositoryTest {

    @Autowired OrderRepository orderRepository;

    @Test
    void should_findOrdersByCustomerAndStatus() {
        // persist test data, then assert
    }
}
```

#### Integration Tests (`@SpringBootTest` + Testcontainers)
```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
@Testcontainers
class OrderIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @DynamicPropertySource
    static void configureDb(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired TestRestTemplate restTemplate;

    @Test
    void should_createAndFetchOrder_end_to_end() { ... }
}
```

#### Test Rules
- Use `@MockBean` only in `@WebMvcTest` / `@SpringBootTest` — it reloads the context; use `@Mock` in plain unit tests.
- Use **AssertJ** (`assertThat`, `assertThatThrownBy`) — never JUnit's raw `assertEquals`.
- Use **`@Sql`** or **`@BeforeEach` fixtures** for repository tests; never rely on data left by other tests.
- Name all tests: `should_<result>_when_<condition>`.

---

