#!/usr/bin/env python3
"""
Comprehensive test runner for OCR-MCP with multiple test suites and reporting.

This script provides a unified interface for running different types of tests:
- Unit tests: Individual component testing
- Integration tests: MCP tool functionality
- E2E tests: Complete workflow testing
- Benchmark tests: Performance and accuracy measurements
- Quick smoke tests: Fast validation for development

Usage:
    python scripts/run_tests.py [options]

Options:
    --suite {unit,integration,e2e,benchmarks,quick,all}  Test suite to run (default: all)
    --verbose, -v                                        Increase verbosity
    --coverage, -c                                      Generate coverage report
    --html                                              Generate HTML coverage report
    --junit                                              Generate JUnit XML report
    --fail-fast                                         Stop on first failure
    --no-mock-hardware                                   Use real hardware where possible
    --benchmark-only                                     Skip accuracy tests in benchmarks
    --performance-only                                   Skip accuracy tests in performance

Examples:
    # Run all tests
    python scripts/run_tests.py

    # Run only unit tests with coverage
    python scripts/run_tests.py --suite unit --coverage

    # Quick smoke tests for development
    python scripts/run_tests.py --suite quick

    # Performance benchmarks only
    python scripts/run_tests.py --suite benchmarks --benchmark-only
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class TestRunner:
    """Comprehensive test runner for OCR-MCP."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.reports_dir = self.project_root / "reports"
        self.coverage_dir = self.project_root / "htmlcov"

        # Ensure directories exist
        self.reports_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)

    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> bool:
        """Run a command and return success status."""
        try:
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info("SUCCESS: Command completed successfully")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                logger.error(f"FAILED: Command failed with exit code {result.returncode}")
                if result.stdout:
                    print("STDOUT:", result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
                return False

        except subprocess.TimeoutExpired:
            logger.error("TIMEOUT: Command timed out")
            return False
        except Exception as e:
            logger.error(f"ERROR: Command failed with exception: {e}")
            return False

    def run_unit_tests(self, args) -> bool:
        """Run unit tests."""
        logger.info("Running unit tests...")

        cmd = ["python", "-m", "pytest", "tests/unit/", "-v"]

        if args.fail_fast:
            cmd.append("--tb=short")
            cmd.append("--fail-fast")

        if args.coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=term-missing",
                f"--cov-report=html:{self.coverage_dir}",
                "--cov-report=xml"
            ])

        if args.junit:
            cmd.extend(["--junitxml", str(self.reports_dir / "unit-tests.xml")])

        return self.run_command(cmd)

    def run_integration_tests(self, args) -> bool:
        """Run integration tests."""
        logger.info("Running integration tests...")

        cmd = ["python", "-m", "pytest", "tests/integration/", "-v"]

        if args.fail_fast:
            cmd.append("--tb=short")
            cmd.append("--fail-fast")

        if args.coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-append"  # Append to existing coverage
            ])

        if args.junit:
            cmd.extend(["--junitxml", str(self.reports_dir / "integration-tests.xml")])

        return self.run_command(cmd)

    def run_e2e_tests(self, args) -> bool:
        """Run end-to-end tests."""
        logger.info("Running end-to-end tests...")

        cmd = ["python", "-m", "pytest", "tests/e2e/", "-v"]

        if args.fail_fast:
            cmd.append("--tb=short")
            cmd.append("--fail-fast")

        if args.coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-append"  # Append to existing coverage
            ])

        if args.junit:
            cmd.extend(["--junitxml", str(self.reports_dir / "e2e-tests.xml")])

        return self.run_command(cmd)

    def run_benchmark_tests(self, args) -> bool:
        """Run benchmark tests."""
        logger.info("Running benchmark tests...")

        cmd = ["python", "-m", "pytest", "tests/benchmarks/", "-v"]

        if args.benchmark_only:
            # Skip accuracy tests, only run performance benchmarks
            cmd.extend(["-k", "not accuracy"])
        elif args.performance_only:
            # Skip accuracy tests, only run performance benchmarks
            cmd.extend(["-k", "not accuracy"])

        if args.junit:
            cmd.extend(["--junitxml", str(self.reports_dir / "benchmark-tests.xml")])

        return self.run_command(cmd)

    def run_quick_tests(self, args) -> bool:
        """Run quick smoke tests for development."""
        logger.info("Running quick smoke tests...")

        # Run a subset of critical tests
        cmd = [
            "python", "-m", "pytest",
            "tests/unit/test_config.py",
            "tests/unit/test_backend_manager.py",
            "tests/integration/test_ocr_tools.py",
            "-v",
            "--tb=short"
        ]

        if args.coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=term-missing",
                f"--cov-report=html:{self.coverage_dir}"
            ])

        return self.run_command(cmd)

    def run_all_tests(self, args) -> bool:
        """Run all test suites."""
        logger.info("Running all test suites...")

        success = True

        # Run tests in order
        test_suites = [
            ("unit", self.run_unit_tests),
            ("integration", self.run_integration_tests),
            ("e2e", self.run_e2e_tests),
            ("benchmarks", self.run_benchmark_tests)
        ]

        for suite_name, suite_func in test_suites:
            logger.info(f"\n{'='*50}")
            logger.info(f"Starting {suite_name} tests")
            logger.info('='*50)

            if not suite_func(args):
                success = False
                if args.fail_fast:
                    logger.error("Stopping due to --fail-fast")
                    break

        # Generate combined coverage report if requested
        if args.coverage and success:
            logger.info("\nGenerating combined coverage report...")
            cmd = [
                "python", "-m", "coverage", "html",
                f"--directory={self.coverage_dir}",
                "--title", "OCR-MCP Combined Coverage Report"
            ]
            self.run_command(cmd)

        return success

    def show_test_structure(self):
        """Show the test directory structure."""
        logger.info("Test Structure:")

        def print_tree(path: Path, prefix: str = ""):
            if not path.exists():
                return

            for item in sorted(path.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    print(f"{prefix}[DIR] {item.name}/")
                    print_tree(item, prefix + "  ")
                elif item.is_file() and item.suffix == '.py':
                    print(f"{prefix}[FILE] {item.name}")

        print_tree(self.test_dir)

    def main(self):
        """Main entry point."""
        parser = argparse.ArgumentParser(
            description="Comprehensive test runner for OCR-MCP",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=__doc__
        )

        parser.add_argument(
            "--suite",
            choices=["unit", "integration", "e2e", "benchmarks", "quick", "all"],
            default="all",
            help="Test suite to run (default: all)"
        )

        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Increase verbosity"
        )

        parser.add_argument(
            "--coverage", "-c",
            action="store_true",
            help="Generate coverage report"
        )

        parser.add_argument(
            "--html",
            action="store_true",
            help="Generate HTML coverage report"
        )

        parser.add_argument(
            "--junit",
            action="store_true",
            help="Generate JUnit XML report"
        )

        parser.add_argument(
            "--fail-fast",
            action="store_true",
            help="Stop on first failure"
        )

        parser.add_argument(
            "--no-mock-hardware",
            action="store_true",
            help="Use real hardware where possible"
        )

        parser.add_argument(
            "--benchmark-only",
            action="store_true",
            help="Skip accuracy tests in benchmarks"
        )

        parser.add_argument(
            "--performance-only",
            action="store_true",
            help="Skip accuracy tests in performance"
        )

        parser.add_argument(
            "--show-structure",
            action="store_true",
            help="Show test directory structure and exit"
        )

        args = parser.parse_args()

        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        if args.show_structure:
            self.show_test_structure()
            return True

        # Validate test directory exists
        if not self.test_dir.exists():
            logger.error(f"Tests directory not found: {self.test_dir}")
            return False

        # Set environment variables for testing
        os.environ.setdefault("OCR_MCP_TESTING", "1")
        if args.no_mock_hardware:
            os.environ.setdefault("OCR_MCP_REAL_HARDWARE", "1")

        # Run the requested test suite
        suite_map = {
            "unit": self.run_unit_tests,
            "integration": self.run_integration_tests,
            "e2e": self.run_e2e_tests,
            "benchmarks": self.run_benchmark_tests,
            "quick": self.run_quick_tests,
            "all": self.run_all_tests
        }

        success = suite_map[args.suite](args)

        if success:
            logger.info("\nSUCCESS: All tests passed!")
            if args.coverage:
                logger.info(f"Coverage report generated in: {self.coverage_dir}")
            if args.junit:
                logger.info(f"JUnit reports generated in: {self.reports_dir}")
        else:
            logger.error("\nFAILED: Some tests failed!")
            sys.exit(1)

        return success


def main():
    """Entry point for poetry script."""
    runner = TestRunner()
    success = runner.main()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()