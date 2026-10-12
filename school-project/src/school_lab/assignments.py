
import json
from pathlib import Path

from school_lab import Assignment, SubmissionError
from school_lab.parsing import require_fields, require_object, require_string

ASSIGNMENT_FIELDS = frozenset({"assignment_id", "allowed_template", "requirements"})


def parse_assignment(raw: object) -> Assignment:
    data = require_object(raw, "assignment")
    require_fields(data, ASSIGNMENT_FIELDS)

    requirements_raw = data["requirements"]
    if not isinstance(requirements_raw, list):
        raise SubmissionError("schema_error", "requirements", "Ожидается список строк")
    requirements = tuple(
        require_string(item, "requirements[]") for item in requirements_raw
    )

    return Assignment(
        assignment_id=require_string(data["assignment_id"], "assignment_id"),
        allowed_template=require_string(
            data["allowed_template"], "allowed_template", nonempty=False
        ),
        requirements=requirements,
    )


def load_assignments(path: Path) -> dict[str, Assignment]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    data = require_object(raw, "assignments_file")

    items_raw = data.get("assignments")
    if not isinstance(items_raw, list):
        raise SubmissionError("schema_error", "assignments", "Ожидается список")

    result: dict[str, Assignment] = {}
    for item in items_raw:
        assignment = parse_assignment(item)
        result[assignment.assignment_id] = assignment
    return result