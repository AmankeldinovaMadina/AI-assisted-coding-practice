# CAL-102: Back-to-back meetings reported as conflicting

**Type:** bug · **Priority:** medium

## Report

A protected commitment ends at 10:00. A new meeting starts at 10:00, but our interval compatibility helper reports a conflict. Product confirms there is no buffer between meetings.

The same symptom occurs when a meeting ends exactly when a protected commitment begins. Investigate the shared interval helper independently of the unfinished batch-selection feature.

## Acceptance criteria

- `[09:00, 10:00)` and `[10:00, 11:00)` do not overlap in either argument order.
- Genuine partial overlap, containment, and identical intervals still conflict.
- Disjoint intervals stay compatible.
- Equivalent instants expressed with different UTC offsets behave consistently.
- Add regression tests; preserve signatures and positive-length interval assumptions.
