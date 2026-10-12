
import math
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from .errors import AnalysisFailure
from .hashing import stable_hash, submission_hash
from .models import (
    AnalysisContext,
    AnalysisReport,
    Evidence,
    Finding,
    Submission,
)


def validate_report(report: AnalysisReport, value: Submission, ctx: AnalysisContext) -> None:
    if not isinstance(report, AnalysisReport):
        raise AnalysisFailure("Ожидается AnalysisReport")
    if report.submission_id != value.submission_id or report.submission_hash != submission_hash(value):
        raise AnalysisFailure("Отчёт ссылается на другую версию сдачи")
    if report.config_hash != stable_hash(ctx.config_payload()):
        raise AnalysisFailure("Отчёт использует другую конфигурацию")
    if not report.report_id or not report.analyzer_id or not report.analyzer_version:
        raise AnalysisFailure("Идентификаторы отчёта и анализатора обязательны")
    if type(report.review_required) is not bool:
        raise AnalysisFailure("review_required должен быть bool")
    try:
        created = datetime.fromisoformat(report.created_at)
    except (ValueError, TypeError) as exc:
        raise AnalysisFailure("Время отчёта имеет неверный формат") from exc
    if created.tzinfo is None or created.utcoffset() is None:
        raise AnalysisFailure("Часовой пояс времени отчёта обязателен")
    for finding in report.findings:
        if finding.kind not in {"similarity", "rubric_feedback", "processing_error"}:
            raise AnalysisFailure("Неизвестный kind")
        if finding.score is not None and (
                type(finding.score) not in (int, float)
                or not math.isfinite(finding.score)
                or not 0 <= finding.score <= 1
        ):
            raise AnalysisFailure("score должен быть конечным числом 0–1 либо None")
        if not finding.explanation.strip():
            raise AnalysisFailure("Объяснение наблюдения обязательно")
        for evidence in finding.evidence:
            if evidence.submission_id != value.submission_id or evidence.field not in {"text", "code"}:
                raise AnalysisFailure("Evidence ссылается на неизвестный объект или поле")
            lines = getattr(value, evidence.field).splitlines()
            if type(evidence.start_line) is not int or type(evidence.end_line) is not int:
                raise AnalysisFailure("Номер строки должен быть int")
            if not 1 <= evidence.start_line <= evidence.end_line <= len(lines):
                raise AnalysisFailure("Evidence выходит за границы исходного текста")


def make_report(value: Submission, ctx: AnalysisContext, analyzer_id: str, version: str,
                findings: tuple[Finding, ...], *, review_required: bool = False) -> AnalysisReport:
    report = AnalysisReport(
        report_id=str(uuid4()),
        submission_id=value.submission_id,
        submission_hash=submission_hash(value),
        analyzer_id=analyzer_id,
        analyzer_version=version,
        config_hash=stable_hash(ctx.config_payload()),
        findings=findings,
        created_at=datetime.now(UTC).isoformat(),
        review_required=review_required,
    )
    validate_report(report, value, ctx)
    return report


class Analyzer(Protocol):
    @property
    def analyzer_id(self) -> str: ...
    @property
    def analyzer_version(self) -> str: ...
    def analyze(self, submission: Submission, context: AnalysisContext) -> AnalysisReport: ...


def nonempty_line_numbers(text: str) -> tuple[int, ...]:
    return tuple(number for number, line in enumerate(text.splitlines(), 1) if line.strip())


class LengthAnalyzer:
    analyzer_id = "length"
    analyzer_version = "1.0"

    def analyze(self, submission: Submission, context: AnalysisContext) -> AnalysisReport:
        text_lines = nonempty_line_numbers(submission.text)
        code_lines = nonempty_line_numbers(submission.code)
        evidence = tuple(
            Evidence(submission.submission_id, field_name, line_no, line_no)
            for field_name, numbers in (("text", text_lines), ("code", code_lines))
            for line_no in numbers
        )
        finding = Finding(
            kind="rubric_feedback",
            score=None,
            evidence=evidence,
            explanation=(
                f"Непустые строки: text={len(text_lines)}, code={len(code_lines)}. "
                "Длина не оценивает корректность решения."
            ),
        )
        return make_report(submission, context, self.analyzer_id, self.analyzer_version, (finding,))


def template_ranges(source_code: str, template: str) -> tuple[tuple[int, int], ...]:
    if not template.strip():
        return ()
    source_lines = source_code.splitlines()
    template_lines = template.splitlines()
    width = len(template_lines)
    return tuple(
        (index + 1, index + width)
        for index in range(len(source_lines) - width + 1)
        if source_lines[index:index + width] == template_lines
    )


class TemplateAnalyzer:
    analyzer_id = "template"
    analyzer_version = "1.0"

    def analyze(self, submission: Submission, context: AnalysisContext) -> AnalysisReport:
        if submission.assignment_id != context.assignment.assignment_id:
            raise AnalysisFailure("Контекст относится к другому заданию")
        ranges = template_ranges(submission.code, context.assignment.allowed_template)
        evidence = tuple(Evidence(submission.submission_id, "code", s, e) for s, e in ranges)
        explanation = (
            f"Найдены разрешённые блоки шаблона: {len(ranges)}. "
            "Это допустимое совпадение, а не основание санкции."
            if ranges else
            "Точное совпадение с разрешённым шаблоном не найдено. Нечёткое сходство не проверялось."
        )
        finding = Finding("similarity", None, evidence, explanation)
        return make_report(submission, context, self.analyzer_id, self.analyzer_version, (finding,))


class DeclarationAnalyzer:

    analyzer_id = "declaration"
    analyzer_version = "1.0"

    def analyze(self, submission: Submission, context: AnalysisContext) -> AnalysisReport:
        d = submission.ai_declaration
        if d.used:
            explanation = (
                f"Использование ИИ заявлено. Инструмент: {d.tool}; цель: {d.purpose}. "
                "Требуется ручная проверка."
            )
        else:
            explanation = "Использование ИИ не заявлено. Авторство текста автоматически не определялось."
        finding = Finding("rubric_feedback", None, (), explanation)
        return make_report(
            submission, context, self.analyzer_id, self.analyzer_version, (finding,),
            review_required=d.used and not d.verified_by_student,
        )