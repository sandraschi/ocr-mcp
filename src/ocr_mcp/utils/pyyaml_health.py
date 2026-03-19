"""
PyYAML can be half-installed: `import yaml` works (e.g. after restoring __init__.py) but
`pyyaml-*.dist-info/METADATA` is missing. Then `importlib.metadata.version("pyyaml")` is None
and Hugging Face `transformers` raises:

    ValueError: Unable to compare versions for pyyaml>=5.1: need=5.1 found=None

This module detects that state and can force-reinstall PyYAML to restore dist-info.
"""

from __future__ import annotations

import importlib.metadata
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_DIST_NAMES = ("pyyaml", "PyYAML")


def pyyaml_metadata_version() -> str | None:
    """Return installed PyYAML distribution version, or None if missing or broken."""
    for name in _DIST_NAMES:
        try:
            v = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            continue
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def pyyaml_metadata_healthy() -> bool:
    return pyyaml_metadata_version() is not None


def yaml_module_has_dump() -> bool:
    try:
        import yaml as y

        return getattr(y, "dump", None) is not None
    except Exception:
        return False


def _dist_info_has_metadata(site_packages: Path) -> bool:
    """True if some pyyaml*.dist-info contains a METADATA file."""
    if not site_packages.is_dir():
        return False
    for p in site_packages.glob("pyyaml*.dist-info"):
        if (p / "METADATA").is_file():
            return True
    for p in site_packages.glob("PyYAML*.dist-info"):
        if (p / "METADATA").is_file():
            return True
    return False


def _force_reinstall_pyyaml() -> bool:
    """Run pip/uv to force-reinstall PyYAML. Returns True if subprocess exited 0."""
    attempts: list[list[str]] = [
        [sys.executable, "-m", "pip", "install", "--force-reinstall", "pyyaml>=6.0"],
    ]
    try:
        subprocess.run(
            ["uv", "--version"],
            check=True,
            capture_output=True,
            timeout=30,
        )
        attempts.append(["uv", "pip", "install", "--force-reinstall", "pyyaml>=6.0"])
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass

    for cmd in attempts:
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=300, check=False, text=True)
            if r.returncode == 0:
                try:
                    import importlib

                    importlib.metadata.invalidate_caches()
                except Exception:
                    pass
                return True
            logger.warning(
                "PyYAML reinstall attempt failed (%s): %s",
                " ".join(cmd),
                (r.stderr or r.stdout or "")[:500],
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning("PyYAML reinstall attempt error: %s", e)
    return False


def ensure_pyyaml_distribution_healthy(*, repair: bool = True) -> tuple[bool, str | None]:
    """
    Ensure PyYAML is usable for transformers' dependency check.

    Returns:
        (ok, message) — message set when not ok or after repair attempt.
    """
    if yaml_module_has_dump() and pyyaml_metadata_healthy():
        return True, None

    # Broken metadata but yaml might still import
    if yaml_module_has_dump() and not pyyaml_metadata_healthy():
        msg = (
            "PyYAML module loads but package metadata is missing or broken "
            "(transformers requires importlib.metadata.version('pyyaml'))."
        )
        if not repair:
            return False, msg
        logger.warning("%s Attempting force-reinstall of PyYAML.", msg)
        if _force_reinstall_pyyaml():
            if pyyaml_metadata_healthy():
                return True, "Reinstalled PyYAML; dist-info METADATA restored."
            return False, "PyYAML reinstall finished but metadata version is still missing."
        return (
            False,
            msg
            + " Automatic reinstall failed. Run: uv pip install --force-reinstall pyyaml",
        )

    if not repair:
        return False, "PyYAML not importable or has no dump()."

    if _force_reinstall_pyyaml():
        sys.modules.pop("yaml", None)
        if yaml_module_has_dump() and pyyaml_metadata_healthy():
            return True, "Installed/reinstalled PyYAML."
    return False, "PyYAML missing. Run: uv pip install pyyaml>=6.0"


def site_packages_pyyaml_distinfo_ok() -> bool:
    """Diagnostic: METADATA file present under site-packages (any pyyaml dist-info)."""
    try:
        import site

        for sp in site.getsitepackages():
            if _dist_info_has_metadata(Path(sp)):
                return True
    except Exception:
        pass
    return False
