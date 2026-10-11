from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, IntEnum


class BusinessTier(IntEnum):
    STANDARD = 1
    PRIORITY = 2
    STRATEGIC = 3


class RequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Employee:
    employee_id: str
    organization: str


@dataclass(frozen=True)
class MeetingRequest:
    request_id: str
    requester_key: str
    employee_id: str
    subject: str
    agenda: str
    organization: str
    start: datetime
    end: datetime
    business_tier: BusinessTier
    submitted_at: datetime
    idempotency_key: str
    status: RequestStatus = RequestStatus.PENDING


@dataclass(frozen=True)
class CalendarEvent:
    event_id: str
    subject: str
    start: datetime
    end: datetime
    protected: bool = True
