#!/usr/bin/env python3
"""
OCR-MCP Test Runner

Comprehensive test execution script with multiple test modes,
reporting, and CI/CD integration.
"""

import argparse
import os
import sys
import time
from pathlib import Path


class TestRunner:
    """Advanced test runner for OCR-MCP."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.results = {}

    def run_unit_tests(self, verbose: bool = False, coverage: bool = False) -> int:
        """Run unit tests."""
        print("[UNIT] Running Unit Tests...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/unit/",
            "-v" if verbose else "-q",
            "--tb=short",
            "--strict-markers",
        ]

        if coverage:
            cmd.extend(
                [
                    "--cov=src/ocr_mcp",
                    "--cov-report=html:reports/coverage/unit",
                    "--cov-report=xml:reports/coverage/unit/coverage.xml",
                ]
            )

        return self._run_pytest(cmd)

    def run_integration_tests(self, verbose: bool = False, coverage: bool = False) -> int:
        """Run integration tests."""
        print("[INTEGRATION] Running Integration Tests...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/integration/",
            "-v" if verbose else "-q",
            "--tb=short",
            "--strict-markers",
            "-m",
            "integration",
        ]

        if coverage:
            cmd.extend(
                [
                    "--cov=src/ocr_mcp",
                    "--cov-append",
                    "--cov-report=html:reports/coverage/integration",
                    "--cov-report=xml:reports/coverage/integration/coverage.xml",
                ]
            )

        return self._run_pytest(cmd)

    def run_performance_tests(self, verbose: bool = False) -> int:
        """Run performance tests."""
        print("[PERFORMANCE] Running Performance Tests...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/performance/",
            "-v" if verbose else "-q",
            "--tb=short",
            "--strict-markers",
            "-m",
            "performance",
            "--durations=10",
        ]

        return self._run_pytest(cmd)

    def run_security_tests(self, verbose: bool = False) -> int:
        """Run security tests."""
        print("[SECURITY] Running Security Tests...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/security/",
            "-v" if verbose else "-q",
            "--tb=short",
            "--strict-markers",
            "-m",
            "security",
        ]

        return self._run_pytest(cmd)

    def run_fuzzing_tests(self, verbose: bool = False) -> int:
        """Run fuzzing and property-based tests."""
        print("[FUZZING] Running Fuzzing Tests...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/fuzzing/",
            "-v" if verbose else "-q",
            "--tb=short",
            "--strict-markers",
            "-m",
            "fuzzing",
            "--hypothesis-show-statistics",
        ]

        return self._run_pytest(cmd)

    def run_smoke_tests(self, verbose: bool = False) -> int:
        """Run smoke tests (basic functionality)."""
        print("[SMOKE] Running Smoke Tests...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "-k",
            "smoke or basic",
            "-v" if verbose else "-q",
            "--tb=short",
        ]

        return self._run_pytest(cmd)

    def run_regression_tests(self, verbose: bool = False) -> int:
        """Run regression tests."""
        print("[REGRESSION] Running Regression Tests...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/regression/",
            "-v" if verbose else "-q",
            "--tb=short",
            "--strict-markers",
        ]

        return self._run_pytest(cmd)

    def run_e2e_tests(self, verbose: bool = False) -> int:
        """Run end-to-end tests."""
        print("[E2E] Running End-to-End Tests...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/e2e/",
            "-v" if verbose else "-q",
            "--tb=short",
            "--strict-markers",
            "-m",
            "e2e",
        ]

        return self._run_pytest(cmd)

    def run_all_tests(self, verbose: bool = False, coverage: bool = True) -> int:
        """Run all test suites."""
        print("[ALL] Running Complete Test Suite...")

        test_suites = [
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("Performance Tests", self.run_performance_tests),
            ("Security Tests", self.run_security_tests),
            ("Fuzzing Tests", self.run_fuzzing_tests),
            ("E2E Tests", self.run_e2e_tests),
            ("Regression Tests", self.run_regression_tests),
        ]

        overall_result = 0

        for suite_name, test_func in test_suites:
            try:
                result = test_func(verbose=verbose, coverage=coverage and "Unit" in suite_name)
                if result != 0:
                    overall_result = result
                    print(f"[ERROR] {suite_name} failed with code {result}")
                else:
                    print(f"[OK] {suite_name} passed")
            except Exception as e:
                print(f"[CRASH] {suite_name} crashed: {e}")
                overall_result = 1

        return overall_result

    def run_with_profile(self, test_path: str, profile_output: str = None) -> int:
        """Run tests with profiling."""
        print("[PROFILE] Running Tests with Profiling...")

        import cProfile
        import pstats

        profiler = cProfile.Profile()

        cmd = ["python", "-m", "pytest", test_path, "-q", "--tb=no"]

        profiler.enable()
        result = self._run_pytest(cmd)
        profiler.disable()

        if profile_output:
            stats = pstats.Stats(profiler)
            stats.sort_stats("cumulative")
            stats.dump_stats(profile_output)
            print(f"📈 Profile saved to {profile_output}")

        return result

    def generate_test_report(self, output_dir: str = "reports") -> None:
        """Generate comprehensive test report."""
        print("[REPORT] Generating Test Report...")

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        report = {
            "timestamp": time.time(),
            "test_run": {
                "total_suites": len(self.results),
                "passed_suites": sum(1 for r in self.results.values() if r == 0),
                "failed_suites": sum(1 for r in self.results.values() if r != 0),
            },
            "results": self.results,
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": str(Path.cwd()),
            },
        }

        report_file = output_path / "test_report.json"
        with open(report_file, "w") as f:
            import json

            json.dump(report, f, indent=2)

        print(f"📄 Report saved to {report_file}")

    def _run_pytest(self, cmd: list[str]) -> int:
        """Run pytest command and return exit code."""
        import subprocess

        try:
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=False, text=True)
            return result.returncode
        except Exception as e:
            print(f"[ERROR] Failed to run test command: {e}")
            return 1

    def setup_test_environment(self) -> None:
        """Set up test environment."""
        print("[SETUP] Setting up test environment...")

        # Create necessary directories
        dirs = [
            "reports/coverage",
            "reports/performance",
            "reports/security",
            "test_artifacts",
            "test_logs",
        ]

        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

        # Set environment variables
        current_pythonpath = os.environ.get("PYTHONPATH", "")
        new_pythonpath = str(self.base_dir / "src")
        if current_pythonpath:
            new_pythonpath = f"{new_pythonpath}:{current_pythonpath}"

        os.environ.update(
            {
                "OCR_TESTING": "true",
                "OCR_DISABLE_GPU": "true",
                "PYTHONPATH": new_pythonpath,
            }
        )

        print("[OK] Test environment ready")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="OCR-MCP Test Runner")
    parser.add_argument(
        "mode",
        choices=[
            "unit",
            "integration",
            "performance",
            "security",
            "fuzzing",
            "smoke",
            "regression",
            "e2e",
            "all",
        ],
        help="Test mode to run",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--coverage", action="store_true", default=True, help="Generate coverage reports"
    )
    parser.add_argument("--profile", help="Profile test execution and save to file")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive test report")

    args = parser.parse_args()

    runner = TestRunner()
    runner.setup_test_environment()

    start_time = time.time()

    try:
        if args.profile:
            result = runner.run_with_profile(args.mode, args.profile)
        elif args.mode == "all":
            result = runner.run_all_tests(verbose=args.verbose, coverage=args.coverage)
        elif args.mode == "unit":
            result = runner.run_unit_tests(verbose=args.verbose, coverage=args.coverage)
        elif args.mode == "integration":
            result = runner.run_integration_tests(verbose=args.verbose, coverage=args.coverage)
        elif args.mode == "performance":
            result = runner.run_performance_tests(verbose=args.verbose)
        elif args.mode == "security":
            result = runner.run_security_tests(verbose=args.verbose)
        elif args.mode == "fuzzing":
            result = runner.run_fuzzing_tests(verbose=args.verbose)
        elif args.mode == "smoke":
            result = runner.run_smoke_tests(verbose=args.verbose)
        elif args.mode == "regression":
            result = runner.run_regression_tests(verbose=args.verbose)
        elif args.mode == "e2e":
            result = runner.run_e2e_tests(verbose=args.verbose)
        else:
            print(f"[ERROR] Unknown test mode: {args.mode}")
            return 1

        duration = time.time() - start_time

        if result == 0:
            print(".2f")
        else:
            print(".2f")
        if args.report:
            runner.generate_test_report()

        return result

    except KeyboardInterrupt:
        print("\n[WARNING]  Test run interrupted by user")
        return 130
    except Exception as e:
        print(f"[CRASH] Test runner crashed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
