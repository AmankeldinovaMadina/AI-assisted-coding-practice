# Blike Moomberg's Calendar — candidate pack

An unfamiliar service, a reported problem, and a chance to show how you reason.

Blike's calendar receives more meeting requests than it can accept. Requests are scored, then scheduled in batches around protected commitments. Investigate one ticket, make a bounded change, and prove it works. This independent practice exercise is inspired by workshop screenshots; it is not official Bloomberg material.

## Start here

1. Follow [SETUP.md](SETUP.md) and run the starter suite.
2. Trace a request from submission through storage to batch scheduling.
3. Read the tickets and choose one to investigate first.
4. Explain your hypothesis and intended verification before editing.
5. Add a regression test, make your change, and inspect the final diff.

## Tickets

| Ticket | Type | Report |
| --- | --- | --- |
| [CAL-101](tickets/001-request-retries.md) | Bug | Some employees receive the wrong request on submission |
| [CAL-102](tickets/002-back-to-back-meetings.md) | Bug | Back-to-back slots are classified as conflicting |
| [CAL-103](tickets/003-batch-selection.md) | Feature / optimisation | Implement optimal batch selection |

The starter suite passes. It checks established behavior, but does not cover the two reported regressions. Batch selection intentionally raises `NotImplementedError`; this is the single implementation task. Extend the suite yourself rather than assuming passing starter tests prove a ticket is resolved.

## System map

`service.py` validates submissions, resolves employees, handles retries, and commits batch outcomes. `database.py` stores requests and events in SQLite. `directory.py` is the authoritative local employee lookup. `models.py` defines immutable records and enums. `scheduler.py` owns interval compatibility and batch selection. `scorer.py` supplies a protocol and an opaque local scoring stand-in.

No web server, cloud account, network connection, API key, or external package is needed. Interact with the service directly from Python or tests.

## Existing contracts

- Time intervals are timezone-aware, positive-length, and half-open: `[start, end)`. Compare actual instants, including different UTC offsets.
- An idempotency key belongs to one requester. A valid retry by that requester returns the original stored request, even if the retry payload differs or the request has already been finalized.
- Employee identity and organization come from the directory, not the caller's payload.
- A batch considers every pending request in the snapshot. Accepted requests become events; other pending requests become rejected. Previously finalized requests stay unchanged.
- Every existing calendar event blocks new requests, regardless of its `protected` flag. This version never replaces existing events. The flag distinguishes fixed commitments from meetings accepted by this service for future product work.
- The database and service assume a single worker; concurrent submissions, distributed locking, cancellation, and calendar editing are outside the exercise.
- Low-level database methods expect valid domain records. The service is the submission validation boundary.

## What matters

Plan before editing. Navigate unfamiliar code. Use AI deliberately. Verify what it changes. Explain the failing case, the evidence for your fix, the remaining tradeoffs, and the complexity of your algorithm. Completion percentage is not the signal.

Avoid broad refactors and replacing the opaque scorer. You may add helpers or indexes when justified. Preserve public signatures and database compatibility.
