---
name: cobol-to-quarkus
description: Generate Java (framework-free core + Quarkus service) from an approved Business Rule Card, one rule per method, with tests derived from the card.
---

# Generate Java from an approved Business Rule Card

Input: a card whose rules are `approved`. Refuse to generate from `draft` rules.

## Structure

- **Core module** (plain Java 17, no framework): records for each copybook in use, one method per rule, Javadoc naming the rule id (`BR-<PROGRAM>-NN`).
- **Numeric fidelity**: never use `double`. Use `BigDecimal`, and store every arithmetic result through `CobolDecimal.store(value, integerDigits, scale)` so truncation and high-order overflow match the COBOL receiving field.
- **I/O behind interfaces** (e.g. `RateTable`), so batch, REST and tests reuse the same logic.
- **Quarkus service** wraps the core: REST or batch entry point, configuration, health checks, OpenTelemetry. No business logic in the service layer.

## Tests

- One JUnit test per rule, named after it, using the card's `edge_cases`.
- An end-to-end test of the program flow (ordering, accumulation, counters that are not reset).
- Equivalence tests come from the `equivalence-verify` skill and must pass before deployment.

## Output

Code under `examples/<program>/java/`; update the card's `open_questions` with anything the code had to assume.
