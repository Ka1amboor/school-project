
import argparse
import json
import sys
from pathlib import Path

from .repositories import InMemorySubmissionRepository
from .services import SubmissionService, import_source
from .sources import JSONLSource


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="school-lab", description="Приём учебных сдач из JSONL")
    subcommands = parser.add_subparsers(dest="command", required=True)
    import_command = subcommands.add_parser("import", help="Импорт файла сдач")
    import_command.add_argument("path", type=Path)
    args = parser.parse_args(argv)

    repo = InMemorySubmissionRepository()
    service = SubmissionService(repo)

    try:
        summary = import_source(JSONLSource(args.path), service)
    except (OSError, UnicodeError) as exc:
        print(json.dumps({"code": "source_unavailable", "message": str(exc)}, ensure_ascii=False),
              file=sys.stderr)
        return 2

    print(json.dumps(summary.to_dict(), ensure_ascii=False))
    return 1 if summary.errors else 0


if __name__ == "__main__":
    sys.exit(main())