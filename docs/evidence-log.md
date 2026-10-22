# Evidence log

Dated, verifiable progress. Each entry links to the commit, test run or report that proves it.

| Date | Milestone | Metric | Proof |
| --- | --- | --- | --- |
| 2026-10-21 | `cobol-tools` parses the CardDemo inventory | 31 programs, 15,833 non-comment lines, 0 parse errors | [commit 9999973](https://github.com/fabioalvesalmeida/cobol-modernization-agents/commit/9999973); [CI run](https://github.com/fabioalvesalmeida/cobol-modernization-agents/actions/runs/39834273732) |
| 2026-10-21 | Copybook layouts validated | 11 of 11 copybooks with a declared record length match exactly | [commit 9999973](https://github.com/fabioalvesalmeida/cobol-modernization-agents/commit/9999973) |
| 2026-10-21 | CBACT04C Business Rule Card (draft) | 6 rules, all with cited source lines | `examples/carddemo-cbact04c/business-rule-card.json` |
| 2026-10-21 | CBACT04C Java core | 6 rules implemented; JUnit tests pass on Java 21 | [CI run](https://github.com/fabioalvesalmeida/cobol-modernization-agents/actions/runs/39834273732) |

## Next milestones

| Target | Milestone | Metric to record |
| --- | --- | --- |
| +30 days | GnuCOBOL golden-master harness for CBACT04C | cases generated, fields compared, differences found/resolved |
| +30 days | Quarkus service + container + Kubernetes manifests | image size, startup time, deploy via GitOps |
| +60 days | Five more CardDemo batch programs through the full pipeline | programs, lines, rules, review time, equivalence pass rate |
| +60 days | Analysis agent runs on the whole inventory | rules drafted per program, reviewer corrections per rule |
| +90 days | Technical write-up (preprint / conference talk) | venue, date, link |
| ongoing | External adoption | stars, forks, issues, named users |
