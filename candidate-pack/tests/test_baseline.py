import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from blike_calendar.database import CalendarDatabase
from blike_calendar.directory import EmployeeDirectory
from blike_calendar.models import (
    BusinessTier, CalendarEvent, Employee, RequestStatus,
)
from blike_calendar.scheduler import intervals_overlap, select_requests
from blike_calendar.scorer import DeterministicRelevanceScorer
from blike_calendar.service import SchedulingService


START = datetime(2026, 1, 15, 9, tzinfo=timezone.utc)


class CalendarBaselineTests(unittest.TestCase):
    def setUp(self):
        self.db = CalendarDatabase()
        self.addCleanup(self.db.close)
        self.directory = EmployeeDirectory([Employee("e-101", "Research"),
                                            Employee("e-202", "Sales")])
        self.scorer = DeterministicRelevanceScorer()
        self.service = SchedulingService(self.db, self.directory, self.scorer)

    def submit(self, **changes):
        values = dict(employee_id="e-101", subject="Market outlook", agenda="Discuss",
                      start=START, end=START + timedelta(hours=1),
                      business_tier=BusinessTier.STANDARD, idempotency_key="token",
                      submitted_at=START - timedelta(days=1))
        values.update(changes)
        return self.service.submit_request(**values)

    def test_submit_stores_pending(self):
        request = self.submit()
        self.assertEqual(self.db.get_request(request.request_id), request)
        self.assertEqual(request.status, RequestStatus.PENDING)

    def test_organization_comes_from_directory(self):
        self.assertEqual(self.submit().organization, "Research")

    def test_retry_returns_original(self):
        first = self.submit()
        self.assertEqual(self.submit(subject="Changed"), first)
        self.assertEqual(len(self.db.list_pending()), 1)

    def test_unknown_employee_rejected(self):
        with self.assertRaises(ValueError):
            self.submit(employee_id="missing")

    def test_blank_token_rejected(self):
        with self.assertRaises(ValueError):
            self.submit(idempotency_key="  ")

    def test_naive_interval_rejected(self):
        with self.assertRaises(ValueError):
            self.submit(start=START.replace(tzinfo=None))

    def test_nonpositive_interval_rejected(self):
        for end in (START, START - timedelta(minutes=1)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                self.submit(end=end)

    def test_naive_submission_time_rejected(self):
        with self.assertRaises(ValueError):
            self.submit(submitted_at=START.replace(tzinfo=None))

    def test_event_round_trip(self):
        event = CalendarEvent("event-1", "Protected", START, START + timedelta(hours=1))
        self.db.insert_event(event)
        self.assertEqual(self.db.list_events(), [event])

    def test_pending_excludes_finalized(self):
        request = self.submit()
        self.db.set_status(request.request_id, RequestStatus.REJECTED)
        self.assertEqual(self.db.list_pending(), [])

    def test_scorer_is_stable_and_bounded(self):
        request = self.submit()
        score = self.scorer.score(request)
        self.assertEqual(score, self.scorer.score(replace(request, request_id="other")))
        self.assertTrue(0 <= score <= 100)

    def test_real_overlap(self):
        self.assertTrue(intervals_overlap(START, START + timedelta(hours=2),
                                          START + timedelta(hours=1),
                                          START + timedelta(hours=3)))

    def test_separated_intervals(self):
        self.assertFalse(intervals_overlap(START, START + timedelta(hours=1),
                                           START + timedelta(hours=2),
                                           START + timedelta(hours=3)))

    def test_selection_placeholder(self):
        # Replace this test with selection behavior when implementing CAL-103.
        with self.assertRaises(NotImplementedError):
            select_requests([], [], self.scorer)

    def test_batch_rolls_back_on_storage_failure(self):
        request = self.submit()
        # Isolate existing transaction behavior from the unfinished algorithm.
        with patch("blike_calendar.service.select_requests", return_value=[request]), \
             patch.object(self.db, "insert_event", side_effect=RuntimeError("disk failure")):
            with self.assertRaises(RuntimeError):
                self.service.schedule_batch()
        self.assertEqual(self.db.get_request(request.request_id).status, RequestStatus.PENDING)
        self.assertEqual(self.db.list_events(), [])


if __name__ == "__main__":
    unittest.main()
