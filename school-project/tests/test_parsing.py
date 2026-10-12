
import copy

import pytest

from school_lab.errors import SubmissionError
from school_lab.models import Submission
from school_lab.parsing import parse_submission


def test_parse_valid(raw_submission):

    before = copy.deepcopy(raw_submission)
    result = parse_submission(raw_submission)
    assert isinstance(result, Submission)
    assert result.submission_id == "sub-001"
    assert result.student_id == "student-001"
    assert raw_submission == before




@pytest.mark.parametrize("field, value, expected_code, expected_field", [
    ("schema_version", True, "schema_error", "schema_version"),        # bool вместо int
    ("schema_version", 2, "unsupported_version", "schema_version"),    # неподдерживаемая версия
    ("code", 123, "schema_error", "code"),                             # число вместо строки
    ("student_id", "  ", "schema_error", "student_id"),                # пусто после strip
    ("submitted_at", "2026-09-01T10:00:00", "schema_error", "submitted_at"),  # без TZ
    ("submitted_at", "not-a-date", "schema_error", "submitted_at"),    # неверный формат
])
def test_reject_invalid_fields(raw_submission, field, value, expected_code, expected_field):

    raw_submission[field] = value
    before = copy.deepcopy(raw_submission)
    with pytest.raises(SubmissionError) as exc:
        parse_submission(raw_submission)
    assert exc.value.code == expected_code
    assert exc.value.field == expected_field
    assert raw_submission == before




def test_reject_unknown_field(raw_submission):
    raw_submission["unknown"] = "value"
    with pytest.raises(SubmissionError) as exc:
        parse_submission(raw_submission)
    assert exc.value.code == "schema_error"
    assert exc.value.field == "unknown"




def test_reject_missing_nested_field(raw_submission):

    del raw_submission["ai_declaration"]["tool"]
    with pytest.raises(SubmissionError) as exc:
        parse_submission(raw_submission)
    assert exc.value.code == "schema_error"
    assert "tool" in exc.value.field


def test_reject_unknown_nested_field(raw_submission):
    raw_submission["ai_declaration"]["extra"] = "x"
    with pytest.raises(SubmissionError) as exc:
        parse_submission(raw_submission)
    assert exc.value.code == "schema_error"


def test_reject_string_false_for_bool(raw_submission):

    raw_submission["ai_declaration"]["used"] = "false"
    with pytest.raises(SubmissionError) as exc:
        parse_submission(raw_submission)
    assert exc.value.code == "schema_error"
    assert "used" in exc.value.field


def test_reject_used_true_without_tool(raw_submission):

    raw_submission["ai_declaration"] = {
        "used": True,
        "tool": None,
        "purpose": None,
        "verified_by_student": False,
    }
    with pytest.raises(SubmissionError) as exc:
        parse_submission(raw_submission)
    assert exc.value.code == "schema_error"
    assert exc.value.field == "ai_declaration"




def test_reject_empty_text_and_code(raw_submission):

    raw_submission["text"] = " "
    raw_submission["code"] = "\n"
    with pytest.raises(SubmissionError) as exc:
        parse_submission(raw_submission)
    assert exc.value.code == "schema_error"
    assert exc.value.field == "text/code"




def test_reject_empty_template_id(raw_submission):
    """template_id=' ' — непустая строка, но после strip пусто → ошибка."""
    raw_submission["template_id"] = " "
    with pytest.raises(SubmissionError) as exc:
        parse_submission(raw_submission)
    assert exc.value.code == "schema_error"
    assert exc.value.field == "template_id"




def test_template_id_none_allowed(raw_submission):
    raw_submission["template_id"] = None
    result = parse_submission(raw_submission)
    assert result.template_id is None




def test_reject_repeated_keys_in_json():

    from school_lab.parsing import decode_json
    with pytest.raises(SubmissionError) as exc:
        decode_json('{"student_id": "a", "student_id": "b"}')
    assert exc.value.code == "invalid_json"


def test_reject_nan_in_json():

    from school_lab.parsing import decode_json
    with pytest.raises(SubmissionError) as exc:
        decode_json('{"score": NaN}')
    assert exc.value.code == "invalid_json"


def test_reject_broken_json():
    from school_lab.parsing import decode_json
    with pytest.raises(SubmissionError) as exc:
        decode_json("{broken")
    assert exc.value.code == "invalid_json"