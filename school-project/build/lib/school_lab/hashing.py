"""Стабильный SHA-256 отпечаток."""
import hashlib
import json
from dataclasses import asdict

from .models import Submission


def canonical_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    )


def stable_hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def submission_hash(value: Submission) -> str:
    return stable_hash(asdict(value))