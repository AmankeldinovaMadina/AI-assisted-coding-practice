from __future__ import annotations

import hashlib
from typing import Protocol

from .models import MeetingRequest


class RelevanceScorer(Protocol):
    def score(self, request: MeetingRequest) -> int: ...


class DeterministicRelevanceScorer:
    """A local stand-in for a remote, opaque model."""

    def score(self, request: MeetingRequest) -> int:
        payload = f"{request.subject}\n{request.agenda}\n{request.organization}"
        digest = hashlib.sha256(payload.encode("utf-8")).digest()
        return int.from_bytes(digest[:2], "big") % 101
