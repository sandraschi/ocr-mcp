"""
Optional pip/uv installs for OCR ML dependencies when ``OCR_AUTO_INSTALL_DEPS=1``.

Used by the FastAPI backend and by ``startup_bootstrap`` (MCP server path).
May call ``os.execv`` to restart the process after installing required packages.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from collections.abc import Callable

logger = logging.getLogger(__name__)


def _check_transformers() -> bool:
    try:
        import transformers

        ver = getattr(transformers, "__version__", "0")
        parts = ver.split(".")[:2]
        major = int(parts[0]) if parts else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        return major > 5 or (major == 5 and minor >= 0)
    except Exception:
        return False


def _check_torch() -> bool:
    try:
        import torch  # noqa: F401

        return True
    except Exception:
        return False


def _check_import(module_name: str) -> bool:
    try:
        __import__(module_name.replace("-", "_"))
        return True
    except Exception:
        return False


def _check_yaml() -> bool:
    try:
        from ocr_mcp.utils.pyyaml_health import pyyaml_metadata_healthy, yaml_module_has_dump

        return yaml_module_has_dump() and pyyaml_metadata_healthy()
    except Exception:
        try:
            import yaml

            return hasattr(yaml, "dump")
        except Exception:
            return False


OCR_DEPS_REQUIRED: list[tuple[str, Callable[[], bool]]] = [
    ("transformers>=5.0.0", _check_transformers),
    ("torch", _check_torch),
    ("accelerate", lambda: _check_import("accelerate")),
    ("huggingface-hub", lambda: _check_import("huggingface_hub")),
    ("pyyaml", _check_yaml),
    ("einops", lambda: _check_import("einops")),
    ("addict", lambda: _check_import("addict")),
    ("easydict", lambda: _check_import("easydict")),
    ("diffusers", lambda: _check_import("diffusers")),
]

OCR_DEPS_OPTIONAL: list[tuple[str, Callable[[], bool]]] = [
    ("paddlepaddle", lambda: _check_import("paddle")),
    ("paddleocr", lambda: _check_import("paddleocr")),
]


def get_pip_install_cmd() -> list[str] | None:
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            capture_output=True,
        )
        return [sys.executable, "-m", "pip", "install"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        return ["uv", "pip", "install"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def ensure_ocr_pip_dependencies(log: logging.Logger | None = None) -> None:
    """
    Install missing OCR pip packages, then ``os.execv`` restart if anything was installed.

    Only intended when ``OCR_AUTO_INSTALL_DEPS=1``.
    """
    lg = log or logger
    to_install: list[str] = []
    for pip_spec, check_fn in OCR_DEPS_REQUIRED:
        try:
            ok = check_fn()
        except Exception:
            ok = False
        if not ok:
            to_install.append(pip_spec)
    if to_install:
        install_cmd = get_pip_install_cmd()
        if not install_cmd:
            lg.warning(
                "No pip or uv found. Install OCR deps manually: %s",
                " ".join(to_install),
            )
        else:
            lg.info("Installing missing OCR deps: %s", ", ".join(to_install))
            try:
                subprocess.run(
                    [*install_cmd, *to_install],
                    check=True,
                    capture_output=False,
                )
            except subprocess.CalledProcessError as e:
                lg.warning("Could not auto-install OCR deps: %s", e)
            else:
                lg.info("OCR deps installed. Restarting process...")
                os.execv(sys.executable, sys.argv)
    optional_installed = False
    install_cmd = get_pip_install_cmd()
    for pip_spec, check_fn in OCR_DEPS_OPTIONAL:
        try:
            if check_fn():
                continue
        except Exception:
            pass
        if install_cmd:
            try:
                r = subprocess.run(
                    [*install_cmd, pip_spec],
                    check=False,
                    capture_output=True,
                )
                if r.returncode == 0:
                    optional_installed = True
            except Exception:
                pass
    if optional_installed:
        lg.info("Optional OCR deps (Paddle) installed. Restarting process...")
        os.execv(sys.executable, sys.argv)
