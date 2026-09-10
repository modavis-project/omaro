"""Offline Unicode Script-property lookup backed by a vendored registry."""

from __future__ import annotations

import bisect
import json
from pathlib import Path
from typing import Any


class UnicodeScriptRegistry:
    """Resolve Unicode code points to ISO 15924 script codes."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.unicode_version = data["unicode_version"]
        self.source_uris = tuple(data["source_uris"])
        self.codes: dict[str, str] = data["codes"]
        self.ranges: tuple[tuple[int, int, str], ...] = tuple(
            sorted(
                ((row[0], row[1], row[2]) for row in data["ranges"]),
                key=lambda row: (row[0], row[1], row[2]),
            )
        )
        self._starts = tuple(row[0] for row in self.ranges)

    @classmethod
    def load(cls, path: Path) -> "UnicodeScriptRegistry":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def script_code(self, character: str) -> str:
        codepoint = ord(character)
        index = bisect.bisect_right(self._starts, codepoint) - 1
        if index >= 0:
            start, end, code = self.ranges[index]
            if start <= codepoint <= end:
                return code
        return "Zzzz"

    def observe(self, text: str) -> tuple[list[str], bool]:
        """Return significant scripts and whether Common/Inherited occurred."""
        codes = {self.script_code(character) for character in text}
        common_or_inherited = bool(codes & {"Zyyy", "Zinh"})
        significant = sorted(codes - {"Zyyy", "Zinh"})
        return significant, common_or_inherited
