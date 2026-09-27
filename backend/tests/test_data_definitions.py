"""
Traceability check for `data_definitions.py` — the module's own docstring promises this file
exists and enforces two things: no key defined there goes unused, and no story/tool references a
key that isn't defined. Added 2026-09-27 (`changes/2026-09-26-data-story-chart-variety.md`), the
second real consumer of `data_definitions.py` (after `changes/2026-09-26-story-5-tech-lens.md`'s
first two keys) — writing the test the docstring already promised, rather than letting a second
change land against an unenforced claim.

Deliberately scans the real source tree, not a hardcoded list of "files that use this module" —
the same "read the real registry, don't hardcode" discipline `test_source_licences.py` already
uses for adapter coverage. A new key, or a new consumer, is caught automatically.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv_linux/bin/python ../tests/test_data_definitions.py
    (or, on Windows, ./venv/Scripts/python ../tests/test_data_definitions.py)
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data_definitions import DEFINITIONS  # noqa: E402

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
_DEFINITIONS_FILE = _SRC_DIR / "data_definitions.py"

# A literal DEFINITIONS[...]/DEFINITIONS.get(...) lookup with a quoted key — the risky, typo-prone
# construct (a hardcoded string that must exactly match a dict key). Deliberately does NOT try to
# catch an indirect lookup built from a variable (e.g. `DEFINITIONS[k] for k in keys`) — that
# pattern can't be verified statically without executing it, and every real key it can ever
# resolve to is still added as its own literal string elsewhere (e.g. `keys.add("some.key")`),
# which the "referenced somewhere" check below already covers.
_BRACKET_LOOKUP = re.compile(r"""DEFINITIONS(?:\[\s*|\.get\(\s*)(["'])([^"']+)\1""")


def _source_files() -> list[Path]:
    return [
        p for p in _SRC_DIR.rglob("*.py")
        if p != _DEFINITIONS_FILE and "venv" not in p.parts and "__pycache__" not in p.parts
    ]


def _source_texts() -> dict[Path, str]:
    return {p: p.read_text(encoding="utf-8") for p in _source_files()}


def test_every_key_is_referenced_somewhere():
    # Every key in DEFINITIONS must appear, quoted, in at least one file that isn't
    # data_definitions.py itself — whether via DEFINITIONS["key"] or a dynamic-lookup builder
    # like keys.add("key"). A key defined but never referenced is dead text nobody will ever
    # see — the exact failure mode the module docstring names.
    texts = _source_texts()
    unused = [
        key for key in DEFINITIONS
        if not any(f'"{key}"' in text or f"'{key}'" in text for text in texts.values())
    ]
    assert not unused, (
        f"data_definitions.py defines these keys but nothing in backend/src references them: "
        f"{unused}. Either wire them into a story/tool, or remove the key."
    )


def test_every_bracket_lookup_resolves_to_a_real_key():
    # The reverse check — a literal DEFINITIONS["typo"] anywhere in the codebase would only
    # surface as a runtime KeyError the first time that code path actually runs (and this
    # backend has no live database in this environment to exercise every path against).
    # Catch it statically instead.
    bad: dict[str, list[str]] = {}
    for path, text in _source_texts().items():
        for _, key in _BRACKET_LOOKUP.findall(text):
            if key not in DEFINITIONS:
                bad.setdefault(key, []).append(str(path.relative_to(_SRC_DIR)))
    assert not bad, (
        f"These files look up a data_definitions.py key that doesn't exist: {bad}. "
        f"Either add the key, or fix the typo."
    )


def test_definitions_are_plain_non_empty_strings():
    # Rule 1 of the module docstring: pure constants, no formatting logic. A key whose value
    # is empty, or isn't a plain string, breaks that contract silently until something tries
    # to render it.
    for key, value in DEFINITIONS.items():
        assert isinstance(value, str), f"{key}'s value is not a plain string: {type(value)!r}"
        assert value.strip(), f"{key}'s value is empty or whitespace-only."


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print(f"\n{len(tests)} tests passed.")
