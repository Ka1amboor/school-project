from pathlib import Path

from school_lab.repositories import InMemorySubmissionRepository
from school_lab.services import SubmissionService, import_source
from school_lab.sources import JSONLSource

DATA = Path(__file__).parent.parent / "data"


def test_valid_corpus_imports():
    repo = InMemorySubmissionRepository()
    service = SubmissionService(repo)
    summary = import_source(JSONLSource(DATA / "submissions.jsonl"), service)
    assert summary.errors == []
    assert len(summary.accepted) == 3


def test_invalid_corpus_reports_all_errors():
    repo = InMemorySubmissionRepository()
    service = SubmissionService(repo)
    summary = import_source(JSONLSource(DATA / "invalid_submissions.jsonl"), service)
    assert summary.accepted == []
    codes = {e["code"] for e in summary.errors}
    assert "schema_error" in codes
    assert "invalid_json" in codes
    assert "unsupported_version" in codes