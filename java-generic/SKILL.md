---
name: java-generic
description: Universal guidelines, patterns, and best practices for Java development. Use when working on any Java project, class, or backend.
version: 2.0.0
kind: guidance
triggers:
  - "work on java project"
  - "create java class"
  - "java backend"
intent: execution
guardrails:
  - "Do not use System.out.println; always use SLF4J with a concrete backend (Logback or Log4j2)."
  - "Manage all dependencies via Maven (`pom.xml`) or Gradle (`build.gradle`). Never install JARs manually."
  - "Strictly adhere to OOP principles and SOLID design."
  - "Do not swallow checked exceptions; handle them with context-rich logging, or wrap and rethrow as domain-specific unchecked exceptions."
  - "Prefer immutability: `final` fields, `List.of()` / `Map.of()` / `Set.of()`, and records for pure data carriers."
  - "Never use raw types; always parameterize generics (`List<String>`, not `List`)."
tools:
  - bash
created_at: 2026-05-30
updated_at: 2026-07-29
---

# Java development guidelines

## 0. Java version target

- **Target Java 21 LTS** unless the runtime constrains you to an earlier version.
- Prefer modern constructs over legacy alternatives:
  - **Records** for immutable data carriers instead of boilerplate POJOs.
  - **Sealed classes/interfaces** to model closed hierarchies (replacing `enum` abuse).
  - **Pattern matching** (`instanceof` patterns, arrow-arm `switch`) over verbose `if-else` chains.
  - **Text blocks** (`"""..."""`) for multiline SQL, JSON templates, etc.
  - **`var`** where the type is obvious from context.
  - **Virtual threads** (`Executors.newVirtualThreadPerTaskExecutor()`) for I/O-bound concurrency; do not hand-manage pools for such workloads.
  - **`SequencedCollection`** when ordering guarantees matter.

## 1. Environment & SDKMAN
- **SDKMAN** manages Java, Maven, and Gradle on Linux and macOS.
- Check for and use these if set: `SDKMAN_DIR`, `SDKMAN_CANDIDATES_DIR`,
  `SDKMAN_PLATFORM`, `JAVA_HOME`, and the version-specific `JAVA11_HOME`,
  `JAVA17_HOME`, `JAVA21_HOME`.

## 2. Build tools & execution
- Always use the project wrapper (`./mvnw`, `./gradlew`) to compile, test, package.
- Never rely on a globally installed Maven or Gradle unless it is explicitly
  managed through SDKMAN — version mismatches follow.
- In multi-module projects run from the root; target submodules explicitly with
  `-pl` (Maven) or `:module:task` (Gradle) only when intentional.

## 3. Project structure
- Standard layout: `src/main/java`, `src/main/resources`, `src/test/java`
  (mirroring main packages), `src/test/resources`.
- For Spring Boot, layer as `controller`/`web` → `service` →
  `repository`/`persistence` → `domain`/`model`. Each layer stays ignorant of
  those above it; domain objects must not import Spring annotations.

## 4. Testing
- **JUnit 5** with `@ExtendWith(MockitoExtension.class)`, plus **Mockito**.
- **AssertJ** for fluent assertions; avoid bare `assertEquals` chains.
- **Testcontainers** for integration tests needing real databases, brokers, or services.
- Tests mirror the exact package path of the class under test.
- Name methods `should_<expectedBehavior>_when_<condition>`.
- Target branch coverage on core business logic; do not fixate on line coverage.

## 5. Logging
- **SLF4J** as the facade, bound to **Logback** or **Log4j2**.
- Log real context (entity IDs, correlation IDs, operation names), not generic
  "success"/"failed".
- Parameterized statements only: `log.debug("Fetching user id={}", userId)` —
  never concatenation.
- `DEBUG`/`TRACE` for entry/exit on complex logic, `INFO` for significant state
  transitions, `WARN`/`ERROR` for recoverable/unrecoverable failures.
- Always include the stack trace: `log.error("Operation failed for id={}", id, e)`.

## 6. Code style & formatting
- **Spotless** with **Google Java Format** or **Palantir Java Format**, run in the
  build (`spotless:apply`). Let tooling enforce style, not review.
- Honour any `checkstyle.xml` present for structural rules.
- **Never** use fully qualified class names inline — import instead:
  - ❌ `java.util.List<String> list = new java.util.ArrayList<>();`
  - ✅ `List<String> list = new ArrayList<>();`
- Imports ascending alphabetically, static imports last.
- Prefer `List.of()` / `Map.of()` / `Set.of()` unless mutability is genuinely needed.
- **Never** write long single-line method chains. One call per line, so code fits
  standard screen widths without horizontal scrolling.

## 7. Null safety & Optional
- Return `Optional<T>` from repository/service methods that may legitimately find
  nothing; never return `null` from a public API.
- Never use `Optional` as a field type or method parameter — return type only.
- Annotate with `@NonNull` / `@Nullable` (`org.springframework.lang` or
  `jakarta.annotation`) to make nullability explicit.

## 8. Error handling
- Build a domain exception hierarchy: a base unchecked `AppException extends
  RuntimeException`, with `NotFoundException`, `ValidationException`,
  `ConflictException` and similar beneath it.
- Catch specific exceptions; never silently swallow.
- Translate infrastructure exceptions (`DataAccessException`) at the boundary —
  do not let them leak into the domain or API layer.

## 9. Vulnerability & dependency management
- Scan for CVEs regularly: **OWASP Dependency-Check**
  (`mvn dependency-check:check` / `./gradlew dependencyCheckAnalyze`) in CI, and
  `./mvnw versions:display-dependency-updates` to surface outdated dependencies.
- Use **BOM** imports (`spring-boot-dependencies`, `jackson-bom`) to align
  transitive versions and reduce conflict risk.
- Pin versions explicitly in production; no open ranges (`[1.0,)`).
- Apply **SpotBugs** or **ErrorProne** for analysis beyond style — they catch null
  dereferences, resource leaks, and broken `equals`/`hashCode`.
