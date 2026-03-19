"""Webapp entry point - adds project root to path and runs backend.app"""


def main():
    import sys
    import traceback
    from pathlib import Path

    try:
        # Find project root: ocr_mcp/ -> src/ -> project_root
        package_dir = Path(__file__).resolve().parent
        project_root = package_dir.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from backend.app import main as app_main

        app_main()
    except Exception:
        traceback.print_exc()
        sys.stderr.flush()
        sys.stdout.flush()
        try:
            root = Path(__file__).resolve().parent.parent.parent
            crash_file = root / "backend_crash.txt"
            with open(crash_file, "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
            sys.stderr.write(f"Traceback written to {crash_file}\n")
        except Exception:
            pass
        sys.exit(1)
