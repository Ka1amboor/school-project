import pytest

from school_lab.analyzers import (
    DeclarationAnalyzer,
    LengthAnalyzer,
    TemplateAnalyzer,
    nonempty_line_numbers,
    template_ranges,
    validate_report,
)
from school_lab.errors import AnalysisFailure
from school_lab.models import AnalysisContext, Assignment

ASSIGNMENT = Assignment(
    assignment_id="assignment-01",
    allowed_template="from typing import Iterable\n",
    requirements=("solve",),
)


@pytest.fixture
def context() -> AnalysisContext:
    return AnalysisContext(assignment=ASSIGNMENT)


@pytest.fixture
def stored(service, raw_submission):
    service.accept(raw_submission)
    return service.repository.get("sub-001")




def test_nonempty_lines():
    assert nonempty_line_numbers("\n a \n\n b\n") == (2, 4)
    assert nonempty_line_numbers("") == ()
    assert nonempty_line_numbers("\n\n") == ()


def test_template_ranges():
    assert template_ranges("a\nb\na\nb\n", "a\nb\n") == ((1, 2), (3, 4))
    assert template_ranges("a\n", " \n") == ()
    assert template_ranges("x\n", "a\nb\n") == ()




def test_length_analyzer(stored, context):
    report = LengthAnalyzer().analyze(stored, context)
    validate_report(report, stored, context)
    assert report.analyzer_id == "length"
    assert report.analyzer_version == "1.0"
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.kind == "rubric_feedback"
    assert finding.score is None  # длина не оценивает качество
    assert all(ev.field in {"text", "code"} for ev in finding.evidence)
    assert finding.explanation.strip()




def test_template_analyzer_finds_block(stored, context):
    report = TemplateAnalyzer().analyze(stored, context)
    validate_report(report, stored, context)
    finding = report.findings[0]
    assert finding.kind == "similarity"
    assert len(finding.evidence) >= 1
    ev = finding.evidence[0]
    assert ev.field == "code"
    assert ev.start_line == 1


def test_template_analyzer_rejects_wrong_assignment(stored):
    from school_lab.models import Assignment as A
    wrong_ctx = AnalysisContext(
        assignment=A("assignment-99", "x\n", ("solve",))
    )
    with pytest.raises(AnalysisFailure):
        TemplateAnalyzer().analyze(stored, wrong_ctx)




def test_declaration_analyzer_not_used(service, raw_submission, context):
    # raw_submission использует used=False
    service.accept(raw_submission)
    stored = service.repository.get("sub-001")
    report = DeclarationAnalyzer().analyze(stored, context)
    validate_report(report, stored, context)
    assert report.findings[0].score is None
    assert report.review_required is False


def test_declaration_analyzer_used(service, raw_submission, context):
    raw_submission["ai_declaration"] = {
        "used": True,
        "tool": "учебный помощник",
        "purpose": "обсуждение",
        "verified_by_student": False,
    }
    service.accept(raw_submission)
    stored = service.repository.get("sub-001")
    report = DeclarationAnalyzer().analyze(stored, context)
    validate_report(report, stored, context)
    assert report.review_required is True