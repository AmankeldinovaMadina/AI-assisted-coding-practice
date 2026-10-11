"""Spoiler-bearing acceptance checks; not distributed in the candidate ZIP."""
import itertools
import random
import sys
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "candidate-pack"))

from blike_calendar.database import CalendarDatabase
from blike_calendar.directory import EmployeeDirectory
from blike_calendar.models import (
    BusinessTier, CalendarEvent, Employee, MeetingRequest, RequestStatus,
)
from blike_calendar.scheduler import intervals_overlap, select_requests
from blike_calendar.service import SchedulingService

BASE = datetime(2026, 1, 15, tzinfo=timezone.utc)


def request(key, start=9, end=10, tier=BusinessTier.STANDARD,
            status=RequestStatus.PENDING):
    return MeetingRequest(key, "employee:e-101", "e-101", key, "Agenda", "Research",
                          BASE + timedelta(hours=start), BASE + timedelta(hours=end),
                          tier, BASE, key, status)


def event(start, end, protected=True):
    return CalendarEvent(f"event-{start}-{end}", "Existing",
                         BASE + timedelta(hours=start), BASE + timedelta(hours=end),
                         protected)


class CountingScorer:
    def __init__(self, scores=None):
        self.scores = scores or {}
        self.calls = []

    def score(self, item):
        self.calls.append(item.request_id)
        return self.scores.get(item.request_id, 20)


def overlap(a, b):
    # Independent half-open interval oracle, not the candidate's helper.
    return max(a.start, b.start) < min(a.end, b.end)


def exhaustive_oracle(items, blockers, scores):
    eligible = sorted(
        (r for r in items if r.status == RequestStatus.PENDING
         and not any(overlap(r, e) for e in blockers)),
        key=lambda r: (r.end, r.start, r.request_id),
    )
    best_key, best = (-1, 0), []
    for bits in range(1 << len(eligible)):
        chosen = [r for i, r in enumerate(eligible) if bits & (1 << i)]
        if any(overlap(a, b) for a, b in itertools.combinations(chosen, 2)):
            continue
        utility = sum(100 * int(r.business_tier) + scores[r.request_id] for r in chosen)
        # Among equal totals, exclude the highest differing ordered index.
        key = (utility, -bits)
        if key > best_key:
            best_key, best = key, chosen
    return best


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.db = CalendarDatabase()
        self.addCleanup(self.db.close)
        self.scorer = CountingScorer()
        self.service = SchedulingService(
            self.db, EmployeeDirectory([Employee("e-101", "Research"),
                                        Employee("e-202", "Sales")]), self.scorer,
        )

    def submit(self, employee="e-101", token="same-token", start=9, end=10):
        return self.service.submit_request(
            employee_id=employee, subject="Subject", agenda="Agenda",
            start=BASE + timedelta(hours=start), end=BASE + timedelta(hours=end),
            business_tier=BusinessTier.STANDARD, idempotency_key=token,
            submitted_at=BASE,
        )

    def test_requester_scoped_idempotency(self):
        a = self.submit()
        b = self.submit(employee="e-202")
        self.assertNotEqual(a.request_id, b.request_id)
        self.assertEqual((b.employee_id, b.organization), ("e-202", "Sales"))
        self.assertEqual(len(self.db.list_pending()), 2)

    def test_retry_after_finalization(self):
        a = self.submit()
        self.db.set_status(a.request_id, RequestStatus.ACCEPTED)
        retry = self.submit(start=11, end=12)
        self.assertEqual(retry, replace(a, status=RequestStatus.ACCEPTED))
        self.assertEqual(self.db.connection.execute("SELECT COUNT(*) FROM requests").fetchone()[0], 1)

    def test_half_open_intervals_and_offsets(self):
        a, b = request("a"), request("b", 10, 11)
        for first, second in ((a, b), (b, a)):
            self.assertFalse(intervals_overlap(first.start, first.end, second.start, second.end))
        offset = timezone(timedelta(hours=5))
        self.assertFalse(intervals_overlap(a.start, a.end,
                                          b.start.astimezone(offset), b.end.astimezone(offset)))
        for other in (a, request("inside", 9.25, 9.75), request("partial", 9.5, 11)):
            self.assertTrue(intervals_overlap(a.start, a.end, other.start, other.end))

    def test_empty_and_all_blocked(self):
        self.assertEqual(select_requests([], [], self.scorer), [])
        self.assertEqual(select_requests([request("a")], [event(8, 11)], self.scorer), [])
        self.assertEqual(self.scorer.calls, [])

    def test_greedy_counterexample(self):
        items = [request("long", 9, 11), request("early", 9, 10), request("late", 10, 11)]
        scorer = CountingScorer({"long": 100, "early": 20, "late": 20})
        self.assertEqual([r.request_id for r in select_requests(items, [], scorer)], ["early", "late"])

    def test_ties_exclude_last_prefix_item(self):
        items = [request("b"), request("a")]
        self.assertEqual(select_requests(items, [], self.scorer), [items[1]])
        # Equal utility: one priority meeting vs. two standard meetings.
        items = [request("early", 9, 10), request("long", 9, 11, BusinessTier.PRIORITY),
                 request("late", 10, 11)]
        scorer = CountingScorer({r.request_id: 0 for r in items})
        self.assertEqual(select_requests(items, [], scorer), [items[1]])

    def test_overlapping_unsorted_events_and_adjacency(self):
        items = [request("before", 7, 8), request("inside", 9, 10),
                 request("after", 12, 13), request("span", 7, 13)]
        blockers = [event(10, 12, False), event(8, 11), event(9, 10)]
        self.assertEqual(select_requests(items, blockers, self.scorer), [items[0], items[2]])
        self.assertCountEqual(self.scorer.calls, ["before", "after"])

    def test_statuses_scoring_and_no_mutation(self):
        items = [request("late", 10, 11), request("blocked"),
                 request("done", 12, 13, status=RequestStatus.ACCEPTED),
                 request("rejected", 14, 15, status=RequestStatus.REJECTED)]
        snapshot = list(items)
        blockers = [event(9, 10, False)]
        self.assertEqual(select_requests(items, blockers, self.scorer), [items[0]])
        self.assertEqual(self.scorer.calls, ["late"])
        self.assertEqual(items, snapshot)
        self.assertEqual(blockers, [event(9, 10, False)])

    def test_offset_ordering(self):
        a = request("early", 9, 10)
        b = request("late", 10, 11)
        b = replace(b, start=b.start.astimezone(timezone(timedelta(hours=-7))),
                    end=b.end.astimezone(timezone(timedelta(hours=5))))
        chosen = select_requests([b, a], [], self.scorer)
        self.assertEqual(chosen, [a, b])
        self.assertIs(chosen[1], b)

    def test_random_small_instances_against_exhaustive_oracle(self):
        rng = random.Random(101)
        for case in range(150):
            items = []
            for i in range(rng.randrange(1, 10)):
                start = rng.randrange(0, 10)
                items.append(request(str(i), start, start + rng.randrange(1, 5),
                                     rng.choice(list(BusinessTier)),
                                     rng.choice([RequestStatus.PENDING] * 4 + [RequestStatus.REJECTED])))
            blockers = [event(s, s + rng.randrange(1, 4))
                        for s in (rng.randrange(0, 12) for _ in range(rng.randrange(4)))]
            scores = {r.request_id: rng.choice([0, 20, 100]) for r in items}
            rng.shuffle(items)
            scorer = CountingScorer(scores)
            with self.subTest(case=case):
                self.assertEqual(select_requests(items, blockers, scorer),
                                 exhaustive_oracle(items, blockers, scores))
                expected_calls = [r.request_id for r in items
                                  if r.status == RequestStatus.PENDING
                                  and not any(overlap(r, e) for e in blockers)]
                self.assertCountEqual(scorer.calls, expected_calls)

    def test_batch_persistence_and_second_batch(self):
        first = self.submit()
        competing = self.submit(token="competing")
        chosen = self.service.schedule_batch()
        self.assertEqual(len(chosen), 1)
        winner = min((first, competing), key=lambda r: r.request_id)
        self.assertEqual(chosen[0], replace(winner, status=RequestStatus.ACCEPTED))
        self.assertEqual(len(self.db.list_events()), 1)
        blocked = self.submit(token="blocked")
        adjacent = self.submit(token="adjacent", start=10, end=11)
        second = self.service.schedule_batch()
        self.assertEqual([r.request_id for r in second], [adjacent.request_id])
        self.assertEqual(self.db.get_request(blocked.request_id).status, RequestStatus.REJECTED)
        self.assertEqual(self.db.list_pending(), [])
        self.assertEqual(self.service.schedule_batch(), [])
        self.assertEqual(len(self.db.list_events()), 2)
        self.assertNotIn(blocked.request_id, self.scorer.calls)

    def test_scorer_failure_rolls_back(self):
        first = self.submit()
        class BrokenScorer:
            def score(self, item):
                raise LookupError("scorer unavailable")
        self.service.scorer = BrokenScorer()
        with self.assertRaises(LookupError):
            self.service.schedule_batch()
        self.assertEqual(self.db.get_request(first.request_id).status, RequestStatus.PENDING)
        self.assertEqual(self.db.list_events(), [])

    def test_sqlite_reopen(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calendar.sqlite"
            db = CalendarDatabase(path)
            item = request("persisted")
            db.insert_request(item)
            db.close()
            db = CalendarDatabase(path)
            try:
                self.assertEqual(db.get_request(item.request_id), item)
            finally:
                db.close()
