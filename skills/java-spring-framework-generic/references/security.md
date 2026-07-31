# Spring: Security

Section 9: Spring Security. Load for authentication, authorization, or filter
chain work.

### 9. Spring Security

#### Configuration (Lambda DSL — Spring Security 6+)
```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity          // enables @PreAuthorize, @PostAuthorize
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtFilter;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(AbstractHttpConfigurer::disable)          // stateless API — CSRF not applicable
            .sessionManagement(sm -> sm.sessionCreationPolicy(STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/auth/**", "/actuator/health/**", "/v3/api-docs/**", "/swagger-ui/**").permitAll()
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class)
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint(new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED))
                .accessDeniedHandler((req, res, e) -> res.sendError(HttpServletResponse.SC_FORBIDDEN))
            )
            .build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);  // cost factor 12 — balance of security and latency
    }
}
```

#### Method-Level Authorization
```java
@Service
public class DocumentService {

    @PreAuthorize("hasRole('ADMIN') or @documentSecurity.isOwner(#id, authentication)")
    public Document findById(UUID id) { ... }

    @PreAuthorize("hasAuthority('document:write')")
    public Document update(UUID id, UpdateRequest req) { ... }
}
```

#### Security Rules
- **Never store passwords in plain text** — always encode with `BCryptPasswordEncoder` (min cost 10).
- **Use authority-based access control** (`hasAuthority('resource:action')`) over role-based (`hasRole('ADMIN')`) for fine-grained permissions.
- **Validate and sanitize JWTs** — check signature, issuer, audience, and expiry. Use `spring-security-oauth2-resource-server` for JWT validation rather than rolling your own filter.
- **Rate-limit authentication endpoints** to mitigate brute-force attacks.
- **Never log tokens, passwords, or PII** — scrub sensitive fields in log appenders if necessary.

---

