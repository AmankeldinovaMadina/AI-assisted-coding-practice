# CAL-103: Implement and optimise batch selection

**Type:** feature / optimisation · **Priority:** high

## Context

The service can store requests, but `select_requests` is unfinished. Implement this one function and any helpers you need. First explain a straightforward correct approach, then improve its complexity. A greedy choice of the largest individual score is not generally optimal.

## Selection contract

Inputs are valid immutable domain records with unique request IDs. `requests` can contain finalized records as well as pending ones; `events` can be unsorted and overlapping. Datetimes can use different UTC offsets.

1. Consider only `PENDING` requests.
2. Exclude any request overlapping any existing event. Every event is a blocker, regardless of `protected`.
3. For every remaining request call `scorer.score(request)` exactly once. Never score finalized or blocked requests. Treat it as an expensive, opaque call returning an integer in `[0, 100]`.
4. Define request utility as `100 * int(request.business_tier) + relevance_score`. Maximise the **sum** of utilities over a pairwise compatible subset. This is a weighted sum, not a lexicographic business-tier ranking.
5. Use half-open intervals; meetings may touch at their endpoints.
6. Return the original request objects sorted by `(end, start, request_id)`. Do not mutate input collections, records, or the database.

## Deterministic tie rule

Sort eligible requests by `(end, start, request_id)`. For each prefix, compare the best total excluding its last request against the total including it plus the optimum compatible earlier prefix. **If totals are equal, exclude that last request.** Apply this rule at every prefix. This precisely defines the expected subset without comparing whole lists of IDs.

## Examples

With no events, three STANDARD requests have relevance 20:

| ID | Interval | Utility |
| --- | --- | --- |
| long | 09:00–11:00 | 120 |
| early | 09:00–10:00 | 120 |
| late | 10:00–11:00 | 120 |

Choose `early, late`, with total utility 240. If an event occupies 09:30–10:30, all three are blocked. Two requests with identical intervals and utility are resolved by the ordering and tie rule above.

## Performance target and proof

For `n` requests and `m` events, target **O(n log n + m log m + n log(m + 1)) time** and **O(n + m) space**, excluding scorer internals. Avoid enumerating subsets, scanning every event for every request, or copying a growing selected list at every step. Score calls must stay linear in eligible requests.

Demonstrate correctness on empty input, adjacency, overlapping blockers, a greedy counterexample, equal totals, mixed statuses and offsets, and a second service batch. A small exhaustive oracle is useful for testing random instances. Explain reconstruction as well as computing the optimum value. A large deterministic workload should give practical evidence without a brittle wall-clock assertion.

`schedule_batch` already handles persistence and rollback. Preserve it unless a demonstrated integration defect requires a change. Out-of-contract scorer outputs and concurrent workers are outside scope.
