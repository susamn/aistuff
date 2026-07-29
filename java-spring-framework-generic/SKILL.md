---
name: java-spring-framework-generic
description: >
  Comprehensive guidelines, patterns, and best practices for Spring Boot 3.x
  application development — covering REST APIs, data access, security,
  observability, async patterns, testing, and production readiness.
version: 2.0.0
kind: guidance
triggers:
  - "work on spring boot project"
  - "create spring boot application"
  - "spring rest api"
  - "spring data jpa"
  - "spring security"
  - "spring boot backend"
  - "spring framework"
intent: execution
guardrails:
  - "Target Spring Boot 3.x (Jakarta EE 10+) and Java 21 LTS unless the project is explicitly pinned to an older version."
  - "Always use constructor injection. Never field injection (@Autowired on fields), and setter injection only for genuinely optional dependencies."
  - "Never expose JPA entities from REST controllers. Use dedicated DTO/record types for request and response payloads."
  - "Annotate service-layer write operations with @Transactional. Never annotate controller methods."
  - "Do not use System.out.println. Use SLF4J with parameterized messages."
  - "Never hardcode secrets. Bind @ConfigurationProperties to environment variables or a secrets manager."
  - "Validate incoming payloads with Jakarta Bean Validation (@Valid / @Validated) at the controller boundary — never in the service layer."
  - "When starting a new app, check for an existing OpenAPI schema and build to it. Starting from scratch, write the schema before the implementation."
  - "Always use MockMvc for testing REST controllers."
  - "Use SDKMAN environment variables (JAVA_HOME, JAVA21_HOME, SDKMAN_CANDIDATES_DIR) when present."
  - "Always build via the project wrapper (./mvnw or ./gradlew), never a globally installed tool."
tools:
  - bash
created_at: 2026-05-30
updated_at: 2026-07-29
---

# Spring Boot development guidelines

Spring Boot 3.x on Java 21. The guardrails above apply to every task; the
references below carry the detail for whichever layer you are working in.

## Read next

| file | when |
|---|---|
| `references/foundations.md` | starting or restructuring an app — version baseline, project layout, DI, configuration |
| `references/web-layer.md` | REST controllers and the service layer |
| `references/data-access.md` | repositories, entities, queries, transactions (Spring Data JPA) |
| `references/errors-validation.md` | error responses, exception handlers, request validation |
| `references/security.md` | authentication, authorization, filter chains |
| `references/testing.md` | writing or reviewing tests |
| `references/operations.md` | observability, async/concurrency, domain events, caching |
| `references/api-and-release.md` | OpenAPI documentation, production readiness checklist |

When a task spans layers, load only the references it actually touches — these
are deliberately separable.
