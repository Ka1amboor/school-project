import json
from pathlib import Path

from school_lab.sources import InMemorySource, JSONLSource

PUBLIC = [
    {"submission_id": f"sub-{i:03d}", "student_id": f"s-{i}", "value": i}
    for i in range(1, 4)
]


def test_in_memory_source_order():
    source = InMemorySource(PUBLIC)
    with source.open() as records:
        loaded = list(records)
    assert [r.line_no for r in loaded] == [1, 2, 3]
    assert [r.raw for r in loaded] == PUBLIC


def test_jsonl_source_closes_on_early_exit(tmp_path: Path):
    path = tmp_path / "data.jsonl"
    path.write_text("\n".join(json.dumps(v) for v in PUBLIC) + "\n", encoding="utf-8")
    source = JSONLSource(path)
    with source.open() as records:
        next(records)
    assert source.last_closed is True


def test_jsonl_source_closes_on_exception(tmp_path: Path):
    path = tmp_path / "data.jsonl"
    path.write_text(json.dumps(PUBLIC[0]) + "\n", encoding="utf-8")
    source = JSONLSource(path)
    try:
        with source.open() as records:
            next(records)
            raise RuntimeError("test")
    except RuntimeError:
        pass
    assert source.last_closed is True


def test_jsonl_broken_line_continues(tmp_path: Path):
    path = tmp_path / "data.jsonl"
    path.write_text(
        json.dumps(PUBLIC[0]) + "\n{broken\n" + json.dumps(PUBLIC[1]) + "\n",
        encoding="utf-8",
    )
    source = JSONLSource(path)
    with source.open() as records:
        loaded = list(records)
    assert loaded[0].error is None
    assert loaded[1].error is not None
    assert loaded[1].error.code == "invalid_json"
    assert loaded[2].error is None