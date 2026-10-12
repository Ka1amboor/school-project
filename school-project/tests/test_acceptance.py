import copy

import pytest

from school_lab.errors import SubmissionError


def test_accept_new(service, raw_submission):
    result = service.accept(raw_submission)
    assert result.status == "accepted"
    assert result.submission_id == "sub-001"


def test_duplicate_does_not_increase_count(service, repository, raw_submission):
    service.accept(raw_submission)
    result = service.accept(copy.deepcopy(raw_submission))
    assert result.status == "duplicate"
    assert len(repository) == 1


def test_conflict_does_not_overwrite(service, repository, raw_submission):
    service.accept(raw_submission)
    original = repository.get("sub-001")
    modified = copy.deepcopy(raw_submission)
    modified["text"] = "Другое содержимое"
    with pytest.raises(SubmissionError) as exc:
        service.accept(modified)
    assert exc.value.code == "conflict"
    assert repository.get("sub-001") == original
    assert len(repository) == 1


def test_new_version_new_id(service, repository, raw_submission):
    service.accept(raw_submission)
    v2 = copy.deepcopy(raw_submission)
    v2["submission_id"] = "sub-001-v2"
    v2["text"] = "Новая версия"
    result = service.accept(v2)
    assert result.status == "accepted"
    assert len(repository) == 2


@pytest.mark.parametrize("student_id", ["", " ", None, 42])
def test_reject_bad_student_id(service, repository, raw_submission, student_id):
    raw_submission["student_id"] = student_id
    with pytest.raises(SubmissionError) as exc:
        service.accept(raw_submission)
    assert exc.value.code == "schema_error"
    assert repository.get(raw_submission["submission_id"]) is None