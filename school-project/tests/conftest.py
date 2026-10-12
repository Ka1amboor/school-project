import copy

import pytest

from school_lab.repositories import InMemorySubmissionRepository
from school_lab.services import SubmissionService

RAW_EXAMPLE = {
    "schema_version": 1,
    "submission_id": "sub-001",
    "student_id": "student-001",
    "assignment_id": "assignment-01",
    "submitted_at": "2026-09-01T10:01:00+03:00",
    "text": "Учебное решение с пояснением алгоритма.",
    "code": "from typing import Iterable\n\ndef solve(values: Iterable[int]) -> int:\n    return sum(x * x for x in values if x >= 0)\n",
    "template_id": "template-01",
    "ai_declaration": {
        "used": False,
        "tool": None,
        "purpose": None,
        "verified_by_student": True,
    },
}


@pytest.fixture
def raw_submission() -> dict:
    return copy.deepcopy(RAW_EXAMPLE)


@pytest.fixture
def repository() -> InMemorySubmissionRepository:
    return InMemorySubmissionRepository()


@pytest.fixture
def service(repository) -> SubmissionService:
    return SubmissionService(repository)