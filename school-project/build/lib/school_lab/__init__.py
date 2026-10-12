"""Онлайн-школа: приём сдач и расширяемые анализаторы."""
from .errors import AnalysisFailure, SubmissionError
from .hashing import submission_hash
from .models import (
    AIDeclaration,
    AnalysisContext,
    AnalysisReport,
    Assignment,
    Evidence,
    Finding,
    Submission,
)
from .parsing import parse_submission

__all__ = [
    "AIDeclaration", "AnalysisContext", "AnalysisFailure", "AnalysisReport",
    "Assignment", "Evidence", "Finding", "Submission", "SubmissionError",
    "parse_submission", "submission_hash",
]