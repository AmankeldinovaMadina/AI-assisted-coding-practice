from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .database import CalendarDatabase
from .directory import EmployeeDirectory
from .models import BusinessTier, CalendarEvent, MeetingRequest, RequestStatus
from .scheduler import select_requests
from .scorer import RelevanceScorer


class SchedulingService:
    def __init__(self, database: CalendarDatabase, directory: EmployeeDirectory,
                 scorer: RelevanceScorer):
        self.database = database
        self.directory = directory
        self.scorer = scorer

    def submit_request(
        self, *, employee_id: str, subject: str, agenda: str,
        start: datetime, end: datetime, business_tier: BusinessTier,
        idempotency_key: str, submitted_at: datetime | None = None,
    ) -> MeetingRequest:
        self._validate_interval(start, end)
        if submitted_at is not None and submitted_at.utcoffset() is None:
            raise ValueError("submitted_at must be timezone-aware")
        if not idempotency_key.strip():
            raise ValueError("idempotency_key is required")
        employee = self.directory.require(employee_id)
        requester_key = f"employee:{employee.employee_id}"
        existing = self.database.find_by_idempotency_key(requester_key, idempotency_key)
        if existing is not None:
            return existing
        request = MeetingRequest(
            request_id=str(uuid4()), requester_key=requester_key,
            employee_id=employee.employee_id, subject=subject, agenda=agenda,
            organization=employee.organization, start=start, end=end,
            business_tier=BusinessTier(business_tier),
            submitted_at=submitted_at or datetime.now(timezone.utc),
            idempotency_key=idempotency_key, status=RequestStatus.PENDING,
        )
        self.database.insert_request(request)
        return request

    @staticmethod
    def _validate_interval(start: datetime, end: datetime) -> None:
        if start.utcoffset() is None or end.utcoffset() is None:
            raise ValueError("start and end must be timezone-aware")
        if start >= end:
            raise ValueError("start must be before end")

    def schedule_batch(self) -> list[MeetingRequest]:
        """Finalize all pending requests atomically in this single-worker service."""
        connection = self.database.connection
        connection.execute("BEGIN IMMEDIATE")
        try:
            pending = self.database.list_pending()
            chosen = select_requests(pending, self.database.list_events(), self.scorer)
            chosen_ids = {request.request_id for request in chosen}
            for request in pending:
                accepted = request.request_id in chosen_ids
                self.database.set_status(
                    request.request_id,
                    RequestStatus.ACCEPTED if accepted else RequestStatus.REJECTED,
                )
                if accepted:
                    self.database.insert_event(CalendarEvent(
                        event_id=f"request:{request.request_id}", subject=request.subject,
                        start=request.start, end=request.end, protected=False,
                    ))
            connection.execute("COMMIT")
        except BaseException:
            connection.execute("ROLLBACK")
            raise
        return [self.database.get_request(request.request_id) for request in chosen]
