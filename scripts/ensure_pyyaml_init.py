"""Restore yaml/__init__.py if missing; repair broken PyYAML dist-info.

Run after uv sync: uv run python scripts/ensure_pyyaml_init.py
"""

import sys
from pathlib import Path


def main():
    script_dir = Path(__file__).resolve().parent
    source = script_dir / "venv_fixes" / "yaml_init.py"
    if not source.exists():
        return 0
    try:
        import site

        for sp in site.getsitepackages():
            p = Path(sp)
            if not p.is_absolute():
                continue
            yaml_dir = p / "yaml"
            target = yaml_dir / "__init__.py"
            if yaml_dir.exists() and not target.exists():
                target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
                print("Restored yaml/__init__.py at", target, file=sys.stderr)
    except Exception as e:
        print("ensure_pyyaml_init:", e, file=sys.stderr)

    # Half-installed PyYAML: yaml works but dist-info/METADATA missing (transformers fails)
    try:
        from ocr_mcp.utils.pyyaml_health import ensure_pyyaml_distribution_healthy

        ok, note = ensure_pyyaml_distribution_healthy(repair=True)
        if note:
            print(note, file=sys.stderr if not ok else sys.stdout)
        return 0 if ok else 1
    except Exception as e:
        print("ensure_pyyaml_init (metadata repair):", e, file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
