---
name: cobol-analyze
description: Turn one COBOL program into a reviewable Business Rule Card, citing the exact source lines of every rule. Use before generating any Java code.
---

# Analyze a COBOL program into a Business Rule Card

Output: `business-rule-card.json` valid against `schemas/business-rule-card.schema.json`.

## Rules of evidence

- Every fact comes from a `cobol-tools` MCP call (`program_structure`, `extract_paragraph`, `parse_copybook`). Never describe behavior you did not read.
- Every rule cites its paragraph and line numbers. A rule without lines is not a rule.
- Describe behavior as it **is**, including bugs and placeholders. Mark empty placeholders `not-implemented-in-source`.
- Numeric semantics are mandatory for every arithmetic rule: PIC of operands and result, ROUNDED or truncation, ON SIZE ERROR or silent overflow.
- Anything ambiguous goes to `open_questions`, not into a guessed rule.

## Steps

1. `program_structure(path)` — note kind (batch/online), files, copybooks, the `(MAIN)` flow and the PERFORM graph.
2. `parse_copybook` for each copybook used by a rule — record field layouts.
3. Walk the call graph from `(MAIN)`. For each paragraph with computations, conditions or writes, `extract_paragraph` and write one rule per business decision.
4. Ignore pure plumbing (open/close/status display) unless it changes business behavior (e.g., abend on missing record).
5. `validate_rule_card(card)`; fix every error.
6. Set `review.status` to `in-review`. Only a human reviewer can set rules to `approved`.
