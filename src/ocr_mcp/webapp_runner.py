"""Webapp entry point - adds project root to path and runs backend.app"""


def main():
    import sys
    from pathlib import Path

    # Find project root: ocr_mcp/ -> src/ -> project_root
    package_dir = Path(__file__).resolve().parent
    project_root = package_dir.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from backend.app import main as app_main

    app_main()
