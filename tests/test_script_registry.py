from pathlib import Path

from omaro.script_registry import UnicodeScriptRegistry


def test_unicode_script_registry_observes_representative_characters(repo_root: Path):
    registry = UnicodeScriptRegistry.load(
        repo_root / "data/registries/unicode-script-registry.json"
    )
    assert registry.unicode_version == "17.0.0"
    assert {
        character: registry.script_code(character)
        for character in ("A", "中", "한", "—", "\u0301")
    } == {
        "A": "Latn",
        "中": "Hani",
        "한": "Hang",
        "—": "Zyyy",
        "\u0301": "Zinh",
    }
    assert registry.observe("A—\u0301") == (["Latn"], True)
