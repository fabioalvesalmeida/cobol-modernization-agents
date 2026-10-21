# cobol-modernization-agents

An open reference implementation for **AI-agent-assisted modernization of COBOL applications** into Java services that run on Kubernetes — with every business rule extracted, cited to its source lines, reviewed by a human and verified for behavioral equivalence before it ships.

> Status: early development. The first program migrated end to end is `CBACT04C` (monthly interest posting) from AWS's open-source [CardDemo](https://github.com/aws-samples/aws-mainframe-modernization-carddemo) mainframe sample.

## Why

Many critical systems in banking and government still run on COBOL written decades ago. Rewriting them is risky mainly because the business rules live only in the code, and subtle numeric behavior (truncation, overflow, implied decimals) is easy to change by accident. Large language models can read COBOL quickly, but on their own they can also invent behavior. This project constrains them.

## How it works

```
COBOL + copybooks
      │  cobol-tools MCP server (deterministic parsing: layouts, paragraphs, call graph, computations)
      ▼
Analysis agent ──► Business Rule Card (JSON, every rule cites paragraph + line numbers)
      │                         │
      │                 human review gate  (only a reviewer can approve a rule)
      ▼                         ▼
Generation agent ──► Java core (one method per rule, BigDecimal + COBOL storage semantics)
      │                         └─► Quarkus service ──► container ──► Kubernetes (GitOps)
      ▼
Equivalence agent ──► golden-master runs (GnuCOBOL vs. Java), field-by-field diff
```

| Component | Path | What it does |
| --- | --- | --- |
| `cobol-tools` MCP server | `mcp/` | Inventory, program structure, paragraph extraction, copybook layouts with byte offsets and Java types, rule-card validation |
| Business Rule Card schema | `schemas/` | The contract between analysis, review and generation |
| Agent skills | `skills/` | `cobol-analyze`, `cobol-to-quarkus`, `equivalence-verify` |
| Worked example | `examples/carddemo-cbact04c/` | Rule card + Java core + tests for CBACT04C |

## Results so far

- `cobol-tools` parses all 31 CardDemo programs in `app/cbl` (15,833 non-comment source lines).
- For all 11 CardDemo copybooks that declare their record length in a comment, the computed layout matches it exactly.
- `CBACT04C`: 6 rules extracted with source lines; Java core implements them with COBOL truncation and overflow semantics; unit tests cover each rule.

Progress and metrics are logged in [`docs/evidence-log.md`](docs/evidence-log.md).

## Quick start

```bash
# 1. Get the sample COBOL (not vendored in this repo)
./scripts/fetch-carddemo.sh            # clones into ./vendor/carddemo

# 2. Run the MCP server's analysis directly
cd mcp && pip install -e '.[test]' && pytest -q
python -c "from cobol_tools.analysis import list_programs; print(len(list_programs('../vendor/carddemo/app/cbl')))"

# 3. Register the MCP server with an agent (Claude Code example)
claude mcp add cobol-tools -- cobol-tools

# 4. Build and test the Java core
cd examples/carddemo-cbact04c/java && mvn -q test
```

## Principles

1. **Grounded, not generated, facts.** Agents get program facts from deterministic tools, never from memory.
2. **Traceability.** Every rule cites source lines; every Java method names its rule.
3. **Human approval.** No code is generated from unapproved rules.
4. **Numeric fidelity.** No `double`; every result is stored with the receiving field's COBOL semantics.
5. **Proof before deploy.** Equivalence tests against the original program gate deployment.

## Scope and provenance

Independent personal project. It contains no code or data from any employer; all examples use public, Apache-2.0-licensed sample applications.

## License

Apache License 2.0.
