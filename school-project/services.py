"""Сервисы приёма и анализа, реестр фабрик."""
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Literal

from .analyzers import Analyzer, validate_report
from .errors import AnalysisFailure, SubmissionError
from .hashing import submission_hash
from .models import AnalysisContext, AnalysisReport, Submission
from .parsing import parse_submission
from .repositories import SubmissionRepository
from .sources import SubmissionSource


@dataclass(frozen=True, slots=True)
class Acceptance:
    status: Literal["accepted", "duplicate"]
    submission_id: str
    content_hash: str


class SubmissionService:
    def __init__(self, repository: SubmissionRepository) -> None:
        self.repository = repository

    def accept(self, raw: object) -> Acceptance:
        value = parse_submission(raw)
        digest = submission_hash(value)
        previous = self.repository.get(value.submission_id)
        if previous is not None:
            if submission_hash(previous) != digest:
                raise SubmissionError("conflict", "submission_id", "Для новой версии требуется новый ID")
            return Acceptance("duplicate", value.submission_id, digest)
        self.repository.add(value)
        return Acceptance("accepted", value.submission_id, digest)

    def accept_validated(self, value: Submission) -> Acceptance:
        """Приём уже валидированной модели (для backend-траектории)."""
        digest = submission_hash(value)
        previous = self.repository.get(value.submission_id)
        if previous is not None:
            if submission_hash(previous) != digest:
                raise SubmissionError("conflict", "submission_id", "Для новой версии требуется новый ID")
            return Acceptance("duplicate", value.submission_id, digest)
        self.repository.add(value)
        return Acceptance("accepted", value.submission_id, digest)


@dataclass
class ImportSummary:
    accepted: list[str] = field(default_factory=list)
    duplicate: list[str] = field(default_factory=list)
    errors: list[dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def import_source(source: SubmissionSource, service: SubmissionService) -> ImportSummary:
    summary = ImportSummary()
    with source.open() as records:
        for record in records:
            if record.error is not None:
                summary.errors.append({"line_no": record.line_no, **record.error.to_dict()})
                continue
            try:
                result = service.accept(record.raw)
            except SubmissionError as exc:
                summary.errors.append({"line_no": record.line_no, **exc.to_dict()})
            else:
                target = summary.accepted if result.status == "accepted" else summary.duplicate
                target.append(result.submission_id)
    return summary


class AnalyzerRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], Analyzer]] = {}

    def register(self, name: str, factory: Callable[[], Analyzer]) -> None:
        if not name.strip() or name in self._factories:
            raise AnalysisFailure("Требуется непустое уникальное имя анализатора")
        self._factories[name] = factory

    def create(self, name: str) -> Analyzer:
        try:
            factory = self._factories[name]
        except KeyError as exc:
            raise AnalysisFailure(f"Неизвестный анализатор: {name}") from exc
        analyzer = factory()
        if analyzer.analyzer_id != name:
            raise AnalysisFailure("Имя регистрации не совпадает с analyzer_id")
        return analyzer


class AnalysisService:
    def __init__(self, repository: SubmissionRepository, registry: AnalyzerRegistry) -> None:
        self.repository = repository
        self.registry = registry

    def run(self, submission_id: str, analyzer_name: str, context: AnalysisContext) -> AnalysisReport:
        value = self.repository.get(submission_id)
        if value is None:
            raise AnalysisFailure("Анализ возможен после приёма сдачи")
        if value.assignment_id != context.assignment.assignment_id:
            raise AnalysisFailure("Требуется контекст соответствующего задания")
        analyzer = self.registry.create(analyzer_name)
        report = analyzer.analyze(value, context)
        validate_report(report, value, context)
        if report.analyzer_id != analyzer.analyzer_id or report.analyzer_version != analyzer.analyzer_version:
            raise AnalysisFailure("Отчёт не соответствует вызванному анализатору")
        return report