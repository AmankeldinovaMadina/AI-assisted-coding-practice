"""Run against the candidate's completed implementation; no timing assertions."""
from time import perf_counter

from test_acceptance import CountingScorer, event, request, select_requests


def main():
    count = 20_000
    items = [request(str(i), i, i + 1) for i in range(count)]
    blockers = [event(count + i, count + i + 0.5) for i in range(count)]
    scorer = CountingScorer()
    started = perf_counter()
    chosen = select_requests(list(reversed(items)), list(reversed(blockers)), scorer)
    elapsed = perf_counter() - started
    assert chosen == items
    assert len(scorer.calls) == count and len(set(scorer.calls)) == count
    print(f"Selected {len(chosen):,} requests against {len(blockers):,} blockers "
          f"in {elapsed:.3f}s; {len(scorer.calls):,} scorer calls.")


if __name__ == "__main__":
    main()
