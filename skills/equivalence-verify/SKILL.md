---
name: equivalence-verify
description: Prove the Java implementation behaves like the original COBOL program by running both on the same inputs (golden master) and diffing outputs field by field.
---

# Verify behavioral equivalence (golden master)

## Steps

1. **Build inputs**: generate datasets from the copybook layouts (`parse_copybook`), covering each rule's `edge_cases`: zero, negative, maximum PIC values, missing lookup records, unsorted keys.
2. **Run the COBOL** with GnuCOBOL (`cobc -x`), file assignments mapped to local files. Record outputs as fixed-length records.
3. **Run the Java core** on the same inputs; serialize outputs to the same fixed-length layout.
4. **Diff** field by field using copybook offsets. Any difference is either a Java bug or a card error: fix the card first, then the code.
5. **Report** in `examples/<program>/equivalence-report.md`: number of cases, fields compared, differences found and resolved, compiler version.

## Pass criteria

100% field equality on all generated cases. Document every intentional divergence (e.g., a bug fixed by decision) with reviewer approval.
