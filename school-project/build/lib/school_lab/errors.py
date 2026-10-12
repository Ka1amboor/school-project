"""Доменные исключения."""


class SubmissionError(Exception):
    """Ошибка приёма сдачи: code, field, message."""

    def __init__(self, code: str, field: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "field": self.field, "message": self.message}


class AnalysisFailure(Exception):
    """Ошибка анализа: контракт нарушен или конфигурация несовместима."""