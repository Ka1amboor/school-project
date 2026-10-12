
import copy
import time

from school_lab.hashing import submission_hash
from school_lab.parsing import (
    parse_submission,
)

RAW = {
    "schema_version": 1,
    "submission_id": "sub-001",
    "student_id": "student-001",
    "assignment_id": "assignment-01",
    "submitted_at": "2026-09-01T10:01:00+03:00",
    "text": "Учебное решение с пояснением.",
    "code": "from typing import Iterable\n\ndef solve(values):\n    return sum(x * x for x in values if x >= 0)\n",
    "template_id": "template-01",
    "ai_declaration": {
        "used": False, "tool": None, "purpose": None, "verified_by_student": True,
    },
}


def bench(label: str, n: int, func) -> None:
    start = time.perf_counter()
    for _ in range(n):
        func()
    elapsed = time.perf_counter() - start
    print(f"{label}: {n} итераций за {elapsed:.4f} с "
          f"(~{elapsed / n * 1e6:.1f} мкс/вызов)")


def measure_parse(n: int = 10_000) -> None:
    bench("parse_submission", n, lambda: parse_submission(copy.deepcopy(RAW)))


def measure_hash(n: int = 10_000) -> None:
    sub = parse_submission(copy.deepcopy(RAW))
    bench("submission_hash (SHA-256)", n, lambda: submission_hash(sub))


def measure_min_vs_sorted(n: int = 100_000) -> None:
    values = {f"key_{i:06d}" for i in range(1000)}

    start = time.perf_counter()
    for _ in range(n):
        _ = sorted(values)[0]# noqa: FURB192
    sorted_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(n):
        _ = min(values)
    min_time = time.perf_counter() - start

    print(f"sorted(set)[0]: {n} итераций за {sorted_time:.4f} с")
    print(f"min(set):       {n} итераций за {min_time:.4f} с")
    if min_time > 0:
        print(f"Ускорение min: {sorted_time / min_time:.1f}x")


if __name__ == "__main__":
    measure_parse()
    measure_hash()
    measure_min_vs_sorted()