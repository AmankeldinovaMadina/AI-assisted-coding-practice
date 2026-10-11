from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .models import BusinessTier, CalendarEvent, MeetingRequest, RequestStatus


class CalendarDatabase:
    """Single-worker SQLite store. Callers own multi-statement transactions."""

    def __init__(self, path: str | Path = ":memory:"):
        self.connection = sqlite3.connect(path, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.ensure_schema()

    def ensure_schema(self) -> None:
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS requests (
                request_id TEXT PRIMARY KEY,
                requester_key TEXT NOT NULL,
                employee_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                agenda TEXT NOT NULL,
                organization TEXT NOT NULL,
                start TEXT NOT NULL,
                end TEXT NOT NULL,
                business_tier INTEGER NOT NULL,
                submitted_at TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                status TEXT NOT NULL,
                UNIQUE(requester_key, idempotency_key)
            );
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                start TEXT NOT NULL,
                end TEXT NOT NULL,
                protected INTEGER NOT NULL
            );
        """)

    @staticmethod
    def _request(row: sqlite3.Row) -> MeetingRequest:
        values = dict(row)
        for name in ("start", "end", "submitted_at"):
            values[name] = datetime.fromisoformat(values[name])
        values["business_tier"] = BusinessTier(values["business_tier"])
        values["status"] = RequestStatus(values["status"])
        return MeetingRequest(**values)

    def find_by_idempotency_key(
        self, requester_key: str, idempotency_key: str
    ) -> MeetingRequest | None:
        row = self.connection.execute(
            "SELECT * FROM requests WHERE idempotency_key = ? ORDER BY rowid LIMIT 1",
            (idempotency_key,),
        ).fetchone()
        return self._request(row) if row is not None else None

    def insert_request(self, request: MeetingRequest) -> None:
        values = asdict(request)
        for name in ("start", "end", "submitted_at"):
            values[name] = values[name].isoformat()
        self.connection.execute("""
            INSERT INTO requests VALUES (
                :request_id, :requester_key, :employee_id, :subject, :agenda,
                :organization, :start, :end, :business_tier, :submitted_at,
                :idempotency_key, :status
            )
        """, values)

    def get_request(self, request_id: str) -> MeetingRequest:
        row = self.connection.execute(
            "SELECT * FROM requests WHERE request_id = ?", (request_id,)
        ).fetchone()
        if row is None:
            raise KeyError(request_id)
        return self._request(row)

    def list_pending(self) -> list[MeetingRequest]:
        rows = self.connection.execute(
            "SELECT * FROM requests WHERE status = ? ORDER BY submitted_at, request_id",
            (RequestStatus.PENDING,),
        ).fetchall()
        return [self._request(row) for row in rows]

    def set_status(self, request_id: str, status: RequestStatus) -> None:
        self.connection.execute(
            "UPDATE requests SET status = ? WHERE request_id = ?", (status, request_id)
        )

    def insert_event(self, event: CalendarEvent) -> None:
        self.connection.execute(
            "INSERT INTO events VALUES (?, ?, ?, ?, ?)",
            (event.event_id, event.subject, event.start.isoformat(),
             event.end.isoformat(), int(event.protected)),
        )

    def list_events(self) -> list[CalendarEvent]:
        rows = self.connection.execute("SELECT * FROM events ORDER BY event_id").fetchall()
        return [CalendarEvent(
            event_id=row["event_id"], subject=row["subject"],
            start=datetime.fromisoformat(row["start"]),
            end=datetime.fromisoformat(row["end"]), protected=bool(row["protected"]),
        ) for row in rows]

    def close(self) -> None:
        self.connection.close()
