"""Ship It Friday entry for make.fun.

Writes the single commit-message line to entry.txt in the output
directory ($MAKEFUN_OUTPUT_DIR, default /output). Stdlib only,
deterministic, no network, no side effects beyond the one output file.

Gate (from the competition rules): /output/entry.txt must be UTF-8 text
of 1 to 159 characters, not only white space. The entry is written with
no trailing newline, so the file holds exactly the judged line.

Modes:
  (default)   validate ENTRY, write it, read it back, confirm byte-identical
  --check     validate ENTRY only and exit; writes nothing
  --self-test validate ENTRY and check a byte-identical write/read
              round-trip in a temporary directory, then exit
"""

import argparse
import os
import sys
import tempfile
import unicodedata

ENTRY = (
    "fix: ship it \u2014 tests passed on my machine, "
    "prod is just staging with confidence"
)

MAX_CHARS = 159


def _check_length(text: str) -> list[str]:
    """Reject a line outside the gate's 1-159 character window."""
    problems = []
    if not 1 <= len(text) <= MAX_CHARS:
        problems.append(f"length {len(text)} chars, must be 1-{MAX_CHARS}")
    if not text.strip():
        problems.append("entry is only white space")
    return problems


def _check_single_line(text: str) -> list[str]:
    """A commit message holds one line: no newline, no stray blank edges."""
    problems = []
    if "\n" in text or "\r" in text:
        problems.append("entry must be a single line")
    if text != text.strip():
        problems.append("entry has leading or trailing whitespace")
    if "  " in text:
        problems.append("entry contains a double space")
    return problems


COMMIT_WORDS = (
    "fix:", "ship", "tests", "prod", "staging", "deploy", "merge",
    "commit", "push", "revert", "hotfix", "release",
)


def _check_commit_voice(text: str) -> list[str]:
    """Judge criterion 5: the line must read as a real git commit message
    from a coding agent about to ship. Require commit vocabulary so the
    line cannot be a generic joke in disguise.
    """
    lowered = text.lower()
    if not any(word in lowered for word in COMMIT_WORDS):
        return ["entry does not read as a git commit message"]
    if not text.startswith("fix:"):
        return ["entry should open with a conventional-commit prefix"]
    return []


def _check_friday_ship(text: str) -> list[str]:
    """Judge criteria 3-4: the agent must sound cheerfully unaware of the
    disaster, and the Friday ship-it urge must be in the line.
    """
    lowered = text.lower()
    problems = []
    if "ship" not in lowered:
        problems.append("entry has no ship-it urge")
    if "confidence" not in lowered and "prod" not in lowered:
        problems.append("entry never names production")
    return problems


def _check_ending(text: str) -> list[str]:
    """Reject a line that ends mid-thought or with dangling punctuation."""
    problems = []
    if text.rstrip().endswith((",", ";", ":")):
        problems.append("entry ends with trailing clause punctuation")
    return problems


def _check_no_control_chars(text: str) -> list[str]:
    """Reject invisible control characters: the gate reads plain UTF-8
    text, and a stray control character would corrupt the judged line
    without showing in any editor. The em dash in the entry is
    punctuation (category Pd), not a control character, so it passes.
    """
    bad = sorted({repr(ch) for ch in text if unicodedata.category(ch).startswith("C")})
    if bad:
        return [f"entry contains control characters: {', '.join(bad)}"]
    return []


def validate(text: str) -> list[str]:
    """Return a list of gate failures for `text` (empty means valid)."""
    problems = []
    problems.extend(_check_length(text))
    problems.extend(_check_single_line(text))
    problems.extend(_check_ending(text))
    problems.extend(_check_no_control_chars(text))
    problems.extend(_check_commit_voice(text))
    problems.extend(_check_friday_ship(text))
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:  # pragma: no cover - defensive
        problems.append(f"not encodable as UTF-8: {exc}")
    return problems


def write_entry(out_dir: str) -> str:
    """Write ENTRY to entry.txt under `out_dir`; return the file path."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(ENTRY)
    return path


def read_back(path: str) -> str:
    """Read entry.txt back as UTF-8 text, exactly as the grader would."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def self_test() -> int:
    """Validate ENTRY and verify a byte-identical write/read round-trip."""
    problems = validate(ENTRY)
    if problems:
        print("self-test FAIL: " + "; ".join(problems), file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        path = write_entry(tmp)
        round_tripped = read_back(path)
    if round_tripped != ENTRY:
        print("self-test FAIL: round-trip changed the entry", file=sys.stderr)
        return 1
    print(
        f"self-test OK: {len(ENTRY)} chars, single line, "
        "byte-identical round-trip"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point: validate, then write ENTRY to the output directory."""
    parser = argparse.ArgumentParser(
        description="Write the Ship It Friday entry to entry.txt."
    )
    parser.add_argument(
        "--check", action="store_true", help="validate ENTRY only"
    )
    parser.add_argument(
        "--self-test", action="store_true", help="validate + round-trip test"
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    problems = validate(ENTRY)
    if problems:
        print("validation FAIL: " + "; ".join(problems), file=sys.stderr)
        return 1
    if args.check:
        print(f"check OK: {len(ENTRY)} chars, single line")
        return 0

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = write_entry(out_dir)
    if read_back(path) != ENTRY:
        print("write FAIL: entry.txt differs after write", file=sys.stderr)
        return 1
    print(f"wrote {path} ({len(ENTRY)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
