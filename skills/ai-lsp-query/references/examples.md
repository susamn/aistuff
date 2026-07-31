# Usage examples and skill integration

Concrete invocations, and how other skills call `lsp-query.sh` to get semantic
context before generating or validating code.

### Usage Examples

```bash
# Find all call sites of a function across the project
<SKILL-PATH>/scripts/lsp-query.sh \
  -f src/orders/service.py \
  -q references \
  -s "process_order"

# Get type info at a specific position (0-based line/col)
<SKILL-PATH>/scripts/lsp-query.sh \
  -f internal/handler/order.go \
  -q hover \
  --line 54 --col 12

# Jump-to-definition — where is this declared?
<SKILL-PATH>/scripts/lsp-query.sh \
  -f src/api/routes.py \
  -q definition \
  -s "OrderRepository"

# Full call hierarchy — callers and callees
<SKILL-PATH>/scripts/lsp-query.sh \
  -f internal/service/payment.go \
  -q call-hierarchy \
  -s "Charge"

# List all symbols in a file (functions, classes, methods)
<SKILL-PATH>/scripts/lsp-query.sh \
  -f src/models/order.py \
  -q symbols

# Search workspace for a type name
<SKILL-PATH>/scripts/lsp-query.sh \
  -q workspace-symbols \
  -s "UserRepository" \
  --lang python

# Get all errors/warnings for a file
<SKILL-PATH>/scripts/lsp-query.sh \
  -f src/service/checkout.py \
  -q diagnostics

# Machine-readable JSON output for consumption by another script
<SKILL-PATH>/scripts/lsp-query.sh \
  -f src/orders/service.py \
  -q references \
  -s "process_order" \
  --output json | jq '.locations[]'
```

---

### Integration with Other Skills

`ai-lsp-query` is designed to be called by other skills that need semantic
context before generating or modifying code. The `--output json` flag makes
it pipeable.

**Example: verify a generated method signature matches the actual interface**
```bash
# Get the interface's symbol list as JSON
SYMBOLS=$(
  <SKILL-PATH>/scripts/lsp-query.sh \
    -f src/repository.py \
    -q symbols \
    --output json
)

# Extract method names and pass to a validator
echo "$SYMBOLS" | jq -r '.symbols[] | select(.kind == "Method") | .name'
```

**Example: find all callers before refactoring a function**
```bash
<SKILL-PATH>/scripts/lsp-query.sh \
  -f src/payment/gateway.py \
  -q call-hierarchy \
  -s "charge_card" \
  --output json \
  | jq '.callers[] | "\(.name) at \(.location)"'
```

**Example: check a file for errors after AI-generated edits**
```bash
<SKILL-PATH>/scripts/lsp-query.sh \
  -f src/api/orders.py \
  -q diagnostics \
  --output json \
  | jq '.diagnostics[] | select(.severity == "ERROR")'
```

---

