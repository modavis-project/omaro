"""Offline BCP 47 validation backed by the vendored IANA registry."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALNUM_RE = re.compile(r"^[A-Za-z0-9]+$")


@dataclass(frozen=True)
class LanguageTagAssessment:
    submitted: str
    canonical: str | None
    valid: bool
    status: str
    messages: tuple[str, ...]


class LanguageSubtagRegistry:
    def __init__(self, data: dict[str, Any]) -> None:
        self.file_date = data["file_date"]
        self.source_uri = data["source_uri"]
        self.records: dict[tuple[str, str], dict[str, Any]] = {}
        self.tags: dict[str, dict[str, Any]] = {}
        for record in data["records"]:
            record_type = record["Type"].lower()
            if "Subtag" in record:
                self.records[(record_type, record["Subtag"].lower())] = record
            elif "Tag" in record:
                self.tags[record["Tag"].lower()] = record

    @classmethod
    def load(cls, path: Path) -> "LanguageSubtagRegistry":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    @staticmethod
    def _preferred(record: dict[str, Any], value: str) -> tuple[str, bool]:
        preferred = record.get("Preferred-Value")
        return (str(preferred) if preferred else value, bool(record.get("Deprecated")))

    def assess(self, submitted: str) -> LanguageTagAssessment:
        if not isinstance(submitted, str) or not submitted:
            return LanguageTagAssessment(
                str(submitted), None, False, "invalid", ("empty language tag",)
            )
        lowered = submitted.lower()
        registered_tag = self.tags.get(lowered)
        if registered_tag:
            preferred, deprecated = self._preferred(registered_tag, submitted)
            canonical = preferred if deprecated else registered_tag["Tag"]
            return LanguageTagAssessment(
                submitted,
                canonical,
                True,
                "deprecated"
                if deprecated
                else ("noncanonical" if submitted != canonical else "valid"),
                ("registered grandfathered/redundant tag",),
            )
        parts = submitted.split("-")
        if any(
            not part or len(part) > 8 or not ALNUM_RE.fullmatch(part) for part in parts
        ):
            return LanguageTagAssessment(
                submitted, None, False, "invalid", ("malformed subtag",)
            )
        if parts[0].lower() == "x":
            if len(parts) < 2:
                return LanguageTagAssessment(
                    submitted, None, False, "invalid", ("empty private-use tag",)
                )
            canonical = "-".join(part.lower() for part in parts)
            return LanguageTagAssessment(
                submitted,
                canonical,
                True,
                "noncanonical" if submitted != canonical else "valid",
                ("private-use tag",),
            )

        messages: list[str] = []
        deprecated = False
        language = parts[0].lower()
        language_record = self.records.get(("language", language))
        if not language_record:
            return LanguageTagAssessment(
                submitted,
                None,
                False,
                "invalid",
                (f"unknown language subtag: {parts[0]}",),
            )
        language, was_deprecated = self._preferred(language_record, language)
        deprecated |= was_deprecated
        output = [language.lower()]
        index = 1

        extlang_count = 0
        while index < len(parts) and len(parts[index]) == 3 and parts[index].isalpha():
            record = self.records.get(("extlang", parts[index].lower()))
            if not record or extlang_count == 3:
                break
            value, was_deprecated = self._preferred(record, parts[index].lower())
            output.append(value.lower())
            deprecated |= was_deprecated
            extlang_count += 1
            index += 1

        if index < len(parts) and len(parts[index]) == 4 and parts[index].isalpha():
            script = parts[index].title()
            record = self.records.get(("script", script.lower()))
            if not record:
                return LanguageTagAssessment(
                    submitted,
                    None,
                    False,
                    "invalid",
                    (f"unknown script subtag: {script}",),
                )
            script, was_deprecated = self._preferred(record, script)
            deprecated |= was_deprecated
            if script != language_record.get("Suppress-Script"):
                output.append(script.title())
            else:
                messages.append(f"suppressed redundant script: {script}")
            index += 1

        if index < len(parts) and (
            (len(parts[index]) == 2 and parts[index].isalpha())
            or (len(parts[index]) == 3 and parts[index].isdigit())
        ):
            region = parts[index].upper()
            record = self.records.get(("region", region.lower()))
            if not record:
                return LanguageTagAssessment(
                    submitted,
                    None,
                    False,
                    "invalid",
                    (f"unknown region subtag: {region}",),
                )
            region, was_deprecated = self._preferred(record, region)
            output.append(region.upper())
            deprecated |= was_deprecated
            index += 1

        variants: set[str] = set()
        while index < len(parts):
            part = parts[index]
            is_variant = (5 <= len(part) <= 8) or (len(part) == 4 and part[0].isdigit())
            if not is_variant:
                break
            variant = part.lower()
            record = self.records.get(("variant", variant))
            if not record:
                return LanguageTagAssessment(
                    submitted, None, False, "invalid", (f"unknown variant: {part}",)
                )
            if variant in variants:
                return LanguageTagAssessment(
                    submitted, None, False, "invalid", (f"duplicate variant: {part}",)
                )
            variant, was_deprecated = self._preferred(record, variant)
            output.append(variant.lower())
            variants.add(variant.lower())
            deprecated |= was_deprecated
            index += 1

        singletons: set[str] = set()
        while (
            index < len(parts)
            and len(parts[index]) == 1
            and parts[index].lower() != "x"
        ):
            singleton = parts[index].lower()
            if singleton in singletons or not singleton.isalnum():
                return LanguageTagAssessment(
                    submitted,
                    None,
                    False,
                    "invalid",
                    (f"invalid extension: {singleton}",),
                )
            singletons.add(singleton)
            output.append(singleton)
            index += 1
            start = index
            while index < len(parts) and 2 <= len(parts[index]) <= 8:
                if len(parts[index]) == 1:
                    break
                output.append(parts[index].lower())
                index += 1
            if index == start:
                return LanguageTagAssessment(
                    submitted,
                    None,
                    False,
                    "invalid",
                    (f"empty extension: {singleton}",),
                )

        if index < len(parts) and parts[index].lower() == "x":
            output.append("x")
            index += 1
            if index == len(parts):
                return LanguageTagAssessment(
                    submitted, None, False, "invalid", ("empty private-use sequence",)
                )
            output.extend(part.lower() for part in parts[index:])
            index = len(parts)
        if index != len(parts):
            return LanguageTagAssessment(
                submitted,
                None,
                False,
                "invalid",
                (f"unexpected subtag: {parts[index]}",),
            )

        canonical = "-".join(output)
        status = (
            "deprecated"
            if deprecated
            else ("noncanonical" if submitted != canonical else "valid")
        )
        return LanguageTagAssessment(
            submitted, canonical, True, status, tuple(messages)
        )

    def components(self, language_tag: str) -> dict[str, Any]:
        """Decompose a canonical BCP 47 tag without inventing missing subtags."""
        assessment = self.assess(language_tag)
        if not assessment.valid or assessment.canonical != language_tag:
            raise ValueError(f"language tag is not canonical: {language_tag}")
        parts = language_tag.split("-")
        primary = parts[0].lower()
        language_record = self.records.get(("language", primary), {})
        result: dict[str, Any] = {
            "primary_language_subtag": primary,
            "explicit_script_subtag": None,
            "default_script_subtag": language_record.get("Suppress-Script"),
            "region_subtag": None,
            "variant_subtags": [],
            "extension_subtags": [],
            "private_use_subtags": [],
        }
        index = 1
        while (
            index < len(parts)
            and len(parts[index]) == 3
            and parts[index].isalpha()
            and ("extlang", parts[index].lower()) in self.records
        ):
            index += 1
        if index < len(parts) and len(parts[index]) == 4 and parts[index].isalpha():
            result["explicit_script_subtag"] = parts[index].title()
            index += 1
        if index < len(parts) and (
            (len(parts[index]) == 2 and parts[index].isalpha())
            or (len(parts[index]) == 3 and parts[index].isdigit())
        ):
            result["region_subtag"] = (
                parts[index].upper() if parts[index].isalpha() else parts[index]
            )
            index += 1
        while index < len(parts):
            part = parts[index]
            if (5 <= len(part) <= 8) or (len(part) == 4 and part[0].isdigit()):
                result["variant_subtags"].append(part.lower())
                index += 1
                continue
            break
        while index < len(parts) and len(parts[index]) == 1:
            singleton = parts[index].lower()
            index += 1
            values: list[str] = []
            while index < len(parts) and len(parts[index]) != 1:
                values.append(parts[index].lower())
                index += 1
            if singleton == "x":
                result["private_use_subtags"] = values
                break
            result["extension_subtags"].append("-".join([singleton, *values]))
        return result
