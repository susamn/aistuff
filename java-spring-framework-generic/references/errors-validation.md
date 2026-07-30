# Spring: Errors Validation

Sections 7-8: exception handling and Jakarta Bean Validation. Load when shaping
error responses or validating input at the controller boundary.

### 7. Exception Handling

#### Exception Hierarchy
```java
// Base application exception
public abstract class AppException extends RuntimeException {
    private final HttpStatus status;

    protected AppException(String message, HttpStatus status) {
        super(message);
        this.status = status;
    }

    protected AppException(String message, HttpStatus status, Throwable cause) {
        super(message, cause);
        this.status = status;
    }

    public HttpStatus getStatus() { return status; }
}

// Concrete domain exceptions
public class NotFoundException    extends AppException { public NotFoundException(String m)    { super(m, HttpStatus.NOT_FOUND); } }
public class ConflictException    extends AppException { public ConflictException(String m)    { super(m, HttpStatus.CONFLICT); } }
public class ValidationException  extends AppException { public ValidationException(String m)  { super(m, HttpStatus.BAD_REQUEST); } }
public class ForbiddenException   extends AppException { public ForbiddenException(String m)   { super(m, HttpStatus.FORBIDDEN); } }
```

#### Global Handler with `@RestControllerAdvice`
```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(AppException.class)
    public ResponseEntity<ErrorResponse> handleAppException(AppException ex, HttpServletRequest request) {
        log.warn("Application error at {}: {}", request.getRequestURI(), ex.getMessage());
        return ResponseEntity.status(ex.getStatus())
            .body(new ErrorResponse(ex.getStatus().value(), ex.getMessage(), request.getRequestURI()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException ex, HttpServletRequest request) {
        String detail = ex.getBindingResult().getFieldErrors().stream()
            .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
            .collect(Collectors.joining("; "));
        return ResponseEntity.badRequest()
            .body(new ErrorResponse(400, "Validation failed: " + detail, request.getRequestURI()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleUnexpected(Exception ex, HttpServletRequest request) {
        log.error("Unexpected error at {}", request.getRequestURI(), ex);   // ← always include ex for stack trace
        return ResponseEntity.internalServerError()
            .body(new ErrorResponse(500, "Internal server error", request.getRequestURI()));
    }
}

public record ErrorResponse(int status, String message, String path) {}
```
- **Never leak stack traces, internal class names, or raw exception messages** to API consumers.
- Log unexpected exceptions at `ERROR` level with the full throwable; log expected/business exceptions at `WARN`.

---

### 8. Validation

- Annotate all `@RequestBody` parameters with `@Valid` to trigger Jakarta Bean Validation.
- For service-level method parameter validation, add `@Validated` to the class and `@Valid` to the method parameter.
- Use standard annotations: `@NotNull`, `@NotBlank`, `@NotEmpty`, `@Size`, `@Min`, `@Max`, `@Email`, `@Pattern`.
- For complex cross-field rules, implement a custom `ConstraintValidator<A, T>`:

```java
@Documented
@Constraint(validatedBy = DateRangeValidator.class)
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidDateRange {
    String message() default "End date must be after start date";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
```
- Never duplicate validation logic between the controller and service layers. Validate once at the entry boundary.

---

