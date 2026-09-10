"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .builder import build, package
from .model import Dataset, ValidationError
from .query import query_classifications
from .refresh import refresh_from_legacy


def _repo_root(value: str | None) -> Path:
    return Path(value or ".").resolve()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="omaro")
    result.add_argument(
        "--repo-root", help="repository root (default: current directory)"
    )
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="validate canonical data")
    commands.add_parser("build", help="build all offline distribution formats")
    commands.add_parser("package", help="build the deterministic release archive")
    query = commands.add_parser(
        "query", help="find classification occurrences and explain endorsement offline"
    )
    selector = query.add_mutually_exclusive_group(required=True)
    selector.add_argument(
        "--target-uri", help="exact concept or organological target URI"
    )
    selector.add_argument(
        "--search", help="case-insensitive literal substring in target labels"
    )
    query.add_argument(
        "--context",
        type=Path,
        help="JSON query context; omission evaluates static direct endorsement",
    )
    query.add_argument(
        "--limit",
        type=int,
        default=20,
        choices=range(1, 101),
        metavar="1..100",
        help="maximum targets (default: 20); preserves all their classification occurrences",
    )
    refresh = commands.add_parser(
        "refresh-source", help="intentionally refresh canonical data from MIMO"
    )
    refresh.add_argument("--workers", type=int, default=4, choices=range(1, 9))
    return result


def main(argv: list[str] | None = None) -> int:
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    root = _repo_root(args.repo_root)
    canonical = root / "data" / "canonical"
    schemas = root / "schema"
    output = root / "dist"
    if args.command == "refresh-source":
        summary = refresh_from_legacy(root, canonical, workers=args.workers)
    elif args.command == "query":
        try:
            context = None
            if args.context is not None:
                context = json.loads(args.context.read_text(encoding="utf-8"))
                if not isinstance(context, dict):
                    raise ValidationError("query context must be a JSON object")
            summary = query_classifications(
                Dataset.load(canonical),
                target_uri=args.target_uri,
                search=args.search,
                context=context,
                limit=args.limit,
                schema_dir=schemas,
            )
        except (OSError, json.JSONDecodeError):
            argument_parser.error(
                "cannot read query context or canonical input as valid JSON"
            )
        except ValidationError as exc:
            argument_parser.error(str(exc))
    elif args.command == "validate":
        summary = Dataset.load(canonical).validate(schemas)
    elif args.command == "build":
        summary = build(root, canonical, output, schemas)
    elif args.command == "package":
        dataset = Dataset.load(canonical)
        build(root, canonical, output, schemas)
        archive, checksums = package(root, output, dataset.metadata["dataset_version"])
        summary = {"archive": str(archive), "checksums": str(checksums)}
    else:  # pragma: no cover
        raise AssertionError(args.command)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
