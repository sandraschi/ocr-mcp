"""
Ensure Poppler binaries are discoverable for pdf2image (PDF → raster) on Windows.

pdf2image does not read POPPLER_PATH from the environment; callers pass ``poppler_path``.
We set ``config.poppler_path`` to the directory containing ``pdftoppm``.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from ocr_mcp.core.config import OCRConfig

logger = logging.getLogger(__name__)

_poppler_install_attempted = False


def _pdftoppm_exe_name() -> str:
    return "pdftoppm.exe" if sys.platform == "win32" else "pdftoppm"


def _bin_dir_works(bin_dir: str | Path) -> bool:
    p = Path(bin_dir)
    return (p / _pdftoppm_exe_name()).is_file()


def _which_bin_dir() -> str | None:
    w = shutil.which("pdftoppm")
    if not w:
        return None
    return str(Path(w).resolve().parent)


def _win_candidate_dirs() -> list[Path]:
    out: list[Path] = [
        Path(r"C:\Program Files\poppler\Library\bin"),
        Path(r"C:\Program Files (x86)\poppler\Library\bin"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Poppler" / "Library" / "bin",
    ]
    lad = Path(os.environ.get("LOCALAPPDATA", ""))
    pkg = lad / "Microsoft" / "WinGet" / "Packages"
    if pkg.is_dir():
        for folder in sorted(pkg.glob("*Poppler*")):
            for sub in (folder / "Library" / "bin", folder / "poppler" / "Library" / "bin"):
                out.append(sub)
    return out


def _discover_poppler_bin_dir() -> str | None:
    found = _which_bin_dir()
    if found:
        return found
    if sys.platform == "win32":
        for d in _win_candidate_dirs():
            if _bin_dir_works(d):
                return str(d.resolve())
    return None


def _try_winget_poppler() -> bool:
    if sys.platform != "win32":
        return False
    winget = shutil.which("winget")
    if not winget:
        return False
    cmd = [
        winget,
        "install",
        "-e",
        "--id",
        "oschwartz10612.Poppler",
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--silent",
        "--disable-interactivity",
    ]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            timeout=600,
            check=False,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if r.returncode == 0:
            logger.info("Installed Poppler via winget (oschwartz10612.Poppler).")
            return True
        tail = (r.stderr or r.stdout or "")[-400:]
        logger.debug("winget Poppler install exit %s: %s", r.returncode, tail)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.debug("winget Poppler: %s", e)
    return False


def ensure_poppler_for_pdf(config: OCRConfig) -> None:
    """
    Resolve Poppler bin directory into ``config.poppler_path`` when unset.

    On Windows, may run one silent winget install per process when
    ``OCR_AUTO_INSTALL_POPPLER=1`` (default) and pdftoppm is missing.
    """
    global _poppler_install_attempted

    if os.getenv("OCR_AUTO_INSTALL_POPPLER", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        if not config.poppler_path:
            d = _discover_poppler_bin_dir()
            if d:
                config.poppler_path = d
        return

    env_p = os.getenv("POPPLER_PATH")
    if env_p and _bin_dir_works(env_p):
        config.poppler_path = str(Path(env_p).resolve())
        return

    if config.poppler_path and _bin_dir_works(config.poppler_path):
        return

    d = _discover_poppler_bin_dir()
    if d:
        config.poppler_path = d
        return

    if sys.platform != "win32":
        return

    if _poppler_install_attempted:
        return
    _poppler_install_attempted = True

    logger.info("Poppler (pdftoppm) not found; attempting silent winget install...")
    if _try_winget_poppler():
        d2 = _discover_poppler_bin_dir()
        if d2:
            config.poppler_path = d2
            return
    logger.warning(
        "PDF rasterization may fail without Poppler. "
        "Install: winget install oschwartz10612.Poppler "
        "or set POPPLER_PATH to the folder containing pdftoppm.exe"
    )
