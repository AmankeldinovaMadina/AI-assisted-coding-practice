from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from .models import CalendarEvent, MeetingRequest
from .scorer import RelevanceScorer


def intervals_overlap(
    start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime
) -> bool:
    return start_a <= end_b and start_b <= end_a


def select_requests(
    requests: Sequence[MeetingRequest],
    events: Sequence[CalendarEvent],
    scorer: RelevanceScorer,
) -> list[MeetingRequest]:
    """Choose an optimal compatible subset; see tickets/003-batch-selection.md.

    Inputs are snapshots: do not mutate them or write to the database here.
    """
    raise NotImplementedError("Batch selection is not implemented")
