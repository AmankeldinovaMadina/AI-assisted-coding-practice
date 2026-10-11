# Interviewer materials — spoilers

Keep this directory outside the candidate's editor and AI context until the attempt is complete. These materials are original practice guidance, not Bloomberg's evaluation criteria.

## Planted changes

There are exactly two deliberate defects:

1. `CalendarDatabase.find_by_idempotency_key` ignores `requester_key`, although the database uniqueness constraint correctly scopes keys. Include both fields in the query. Test employee isolation and same-employee retries after finalization.
2. `intervals_overlap` uses inclusive comparisons. For half-open intervals both comparisons must be strict. Test both directions, containment, identical intervals, adjacency, and equivalent instants in different offsets.

The sole missing function is `select_requests`. The reference solution merges blockers, filters candidates using binary search, scores each eligible request once, then uses weighted interval scheduling with binary-searched predecessors and linear-space reconstruction. Its bound is O(m log m + n log(m + 1) + n log n) time and O(n + m) space. Equal totals exclude the last request in the ordered prefix. Scorer internals are deliberately opaque.

## Run acceptance checks

From the repository root, against either the starter or your candidate's implementation:

```sh
python3 -m unittest discover -s interviewer-materials -p 'test_acceptance.py' -v
```

On the untouched starter, failures/errors are expected: the two regression tests fail, and selection tests encounter the placeholder. Two checks also confirm established behavior. On a complete solution, all 13 checks should pass. The random oracle independently enumerates every feasible subset for small inputs and checks the specified tie rule.

## Reveal / apply reference solution

`reference_solution.patch` contains the two fixes and the implementation. It does not alter starter tests. From repository root:

```sh
git apply --check interviewer-materials/reference_solution.patch
git apply interviewer-materials/reference_solution.patch
```

Remove or replace `test_selection_placeholder` in the candidate's starter suite after implementing the feature: it intentionally expects an unimplemented function. The remaining 14 starter tests must still pass. Applying the reference patch to a modified candidate solution may produce conflicts; inspect the patch directly or use a fresh copy of the candidate ZIP.

Optional deterministic scaling exercise after implementing selection:

```sh
python3 interviewer-materials/benchmark.py
```

It runs 20,000 compatible requests against 20,000 irrelevant blockers, checks exact output and scorer-call counts, and reports elapsed time without a machine-dependent time assertion. Inspect the algorithm for asymptotic guarantees; timing alone is not proof.

## Suggested interview prompts

- Ask the candidate to explain the request path and choose a ticket.
- Ask for a small reproduction before implementation.
- If they use AI, ask which claims they independently verified.
- For selection, ask why a locally highest-value meeting can lose globally.
- Ask how equal totals, overlapping events, and second batches are handled.
- Finish with a diff review, regression evidence, and a complexity explanation.

Useful signals: clear hypotheses, bounded changes, tests that fail before and pass after, explicit invariants, inspection of AI output, and honest discussion of incomplete work. Avoid treating all-ticket completion or a particular coding style as the goal.
