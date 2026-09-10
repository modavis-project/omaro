#!/usr/bin/env python3
"""Run the complete suite in bounded processes and verify CI coverage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


GROUPS = ("formats", "package", "replay", "semantics")
BUILD_MODULE = "tests/test_build.py"


def collect() -> list[str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        check=True,
        text=True,
        capture_output=True,
    )
    nodes = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("tests/") and "::" in line
    ]
    if not nodes or len(nodes) != len(set(nodes)):
        raise RuntimeError("Test collection must be nonempty and unique")
    return nodes


def plan(nodes: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {name: [] for name in GROUPS}
    for node in nodes:
        if not node.startswith(BUILD_MODULE + "::"):
            group = "semantics"
        elif node.endswith("::test_release_package_is_complete_and_reproducible"):
            group = "package"
        elif node.endswith("::test_build_is_reproducible_across_processes"):
            group = "replay"
        else:
            group = "formats"
        groups[group].append(node)
    if any(not value for value in groups.values()):
        raise RuntimeError("Every CI group must contain tests")
    return groups


def run(group: str, nodes: list[str], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    report = output / f"{group}.json"
    if report.exists():
        raise RuntimeError(f"Refusing to reuse test receipt: {report}")
    batches: dict[str, list[str]] = {}
    for node in nodes:
        # Corpus builds and their subprocesses must not inherit a previous
        # test's large allocator footprint. Semantic modules are also isolated.
        key = node if node.startswith(BUILD_MODULE + "::") else node.split("::", 1)[0]
        batches.setdefault(key, []).append(node)
    results = []
    for index, (target, expected) in enumerate(batches.items()):
        junit = output / f"{group}-{index}.xml"
        if junit.exists():
            raise RuntimeError(f"Refusing to reuse test output: {junit}")
        print(f"START {group} {index + 1}/{len(batches)}: {target}", flush=True)
        started = time.monotonic()
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-vv",
                target,
                f"--junitxml={junit}",
                "--durations=5",
            ],
            check=True,
        )
        cases = list(ET.parse(junit).getroot().iter("testcase"))
        if len(cases) != len(expected) or any(
            case.find(status) is not None
            for case in cases
            for status in ("failure", "error", "skipped")
        ):
            raise RuntimeError(f"Incomplete successful coverage for {target}")
        peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        peak_mib = peak / (1024 * 1024 if sys.platform == "darwin" else 1024)
        result = {
            "target": target,
            "nodes": expected,
            "passed": len(cases),
            "seconds": round(time.monotonic() - started, 3),
            "childPeakMiBSoFar": round(peak_mib, 2),
        }
        results.append(result)
        print("PASS " + json.dumps(result), flush=True)
    report.write_text(
        json.dumps(
            {"status": "passed", "group": group, "nodes": nodes, "batches": results},
            indent=2,
        )
        + "\n"
    )


def verify(groups: dict[str, list[str]], output: Path) -> None:
    covered: list[str] = []
    for group, expected in groups.items():
        report = json.loads((output / f"{group}.json").read_text())
        if (
            report["status"] != "passed"
            or report["group"] != group
            or report["nodes"] != expected
        ):
            raise RuntimeError(f"Invalid coverage receipt for {group}")
        actual = [node for batch in report["batches"] for node in batch["nodes"]]
        if actual != expected or sum(
            batch["passed"] for batch in report["batches"]
        ) != len(expected):
            raise RuntimeError(f"Incomplete execution receipt for {group}")
        covered.extend(actual)
    if len(covered) != len(set(covered)):
        raise RuntimeError("Duplicate test execution receipts")
    print(
        json.dumps(
            {
                "status": "passed",
                "tests": len(covered),
                "groups": {k: len(v) for k, v in groups.items()},
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=GROUPS)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--verify-reports", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("test-results"))
    args = parser.parse_args()
    groups = plan(collect())
    if args.plan:
        print(json.dumps(groups, indent=2))
    elif args.verify_reports:
        verify(groups, args.output)
    elif args.group:
        run(args.group, groups[args.group], args.output)
    else:
        for group, nodes in groups.items():
            run(group, nodes, args.output)
        verify(groups, args.output)


if __name__ == "__main__":
    main()
