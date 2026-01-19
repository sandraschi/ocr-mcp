#!/usr/bin/env python3
"""
OCR-MCP Development Environment Setup Script

This script sets up the development environment with pre-commit hooks
and other development tools.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], cwd: Path = None) -> bool:
    """Run a command and return success status."""
    try:
        result = subprocess.run(
            command, cwd=cwd or Path.cwd(), capture_output=True, text=True, check=True
        )
        print(f"✓ {' '.join(command)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {' '.join(command)} failed:")
        print(f"  Error: {e.stderr}")
        return False


def main():
    """Set up the development environment."""
    print("🚀 Setting up OCR-MCP Development Environment")
    print("=" * 50)

    project_root = Path(__file__).parent.parent

    # Check if we're in the right directory
    if not (project_root / "pyproject.toml").exists():
        print("❌ Error: Not in OCR-MCP project root directory")
        sys.exit(1)

    print(f"📁 Working directory: {project_root}")

    # Install pre-commit hooks
    print("\n📋 Installing pre-commit hooks...")
    if not run_command(["poetry", "run", "pre-commit", "install"], project_root):
        print("⚠️  Pre-commit installation failed, but continuing...")

    # Install pre-commit hooks
    print("\n🔧 Installing pre-commit hook environments...")
    if not run_command(["poetry", "run", "pre-commit", "install-hooks"], project_root):
        print("⚠️  Pre-commit hooks installation failed, but continuing...")

    # Run pre-commit on all files to check current status
    print("\n🔍 Running pre-commit checks on all files...")
    result = subprocess.run(
        ["poetry", "run", "pre-commit", "run", "--all-files"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ All pre-commit checks passed!")
    else:
        print("⚠️  Some pre-commit checks failed. This is normal for existing code.")
        print("   Run 'poetry run pre-commit run --all-files' to see details.")
        print("   Run 'poetry run pre-commit run --all-files --fix' to auto-fix issues.")

    # Test basic functionality
    print("\n🧪 Testing basic functionality...")

    # Test imports
    try:
        import ocr_mcp

        print("✅ Core imports work")
    except ImportError as e:
        print(f"⚠️  Import test failed: {e}")

    # Test Poetry environment
    if run_command(["poetry", "check"], project_root):
        print("✅ Poetry configuration is valid")
    else:
        print("⚠️  Poetry configuration issues detected")

    print("\n" + "=" * 50)
    print("🎉 Development environment setup complete!")
    print("\n📚 Useful commands:")
    print("  • poetry run pre-commit run --all-files    # Run all checks")
    print("  • poetry run pytest                        # Run tests")
    print("  • poetry run ruff check . --fix           # Fix code issues")
    print("  • poetry run ruff format .                # Format code")
    print("  • poetry run python scripts/run_webapp.py # Start webapp")
    print("  • poetry run python scripts/run_tests.py all # Run full test suite")
    print("\n📖 See README.md and tests/README.md for more information.")


if __name__ == "__main__":
    main()
