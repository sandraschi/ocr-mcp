"""
Ensure the Tesseract OCR binary exists on Windows without prompting the user.

Python side only needs pytesseract + Pillow; the native `tesseract` executable must be present.
If missing, tries silent install: winget, then Chocolatey, then Scoop (whichever is available).
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys

from ocr_mcp.core.config import OCRConfig

logger = logging.getLogger(__name__)

_WIN_TESSERACT_PATHS: tuple[str, ...] = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)

# winget package IDs to try (popular Windows builds)
_WINGET_IDS: tuple[str, ...] = (
    "UB-Mannheim.TesseractOCR",
    "TesseractOCR.Tesseract",
)

# One install attempt per process (avoids repeated UAC / winget spam in a single run)
_install_attempted = False


def _pytesseract_ok(tesseract_cmd: str | None) -> bool:
    try:
        import pytesseract

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _resolve_tesseract_exe(config_cmd: str | None) -> str | None:
    if config_cmd and os.path.isfile(config_cmd):
        return config_cmd
    for p in _WIN_TESSERACT_PATHS:
        if os.path.isfile(p):
            return p
    w = shutil.which("tesseract")
    return w if w else None


def _run_install(cmd: list[str], timeout: int = 600) -> bool:
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            check=False,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if r.returncode == 0:
            return True
        tail = (r.stderr or r.stdout or "")[-400:]
        logger.debug("Install command failed (%s): %s", " ".join(cmd[:6]), tail)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.debug("Install command error: %s", e)
    return False


def _try_winget() -> bool:
    winget = shutil.which("winget")
    if not winget:
        return False
    base = [
        winget,
        "install",
        "-e",
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--silent",
        "--disable-interactivity",
        "--id",
    ]
    for pkg in _WINGET_IDS:
        if _run_install([*base, pkg]):
            logger.info("Installed Tesseract via winget (%s).", pkg)
            return True
    return False


def _try_choco() -> bool:
    choco = shutil.which("choco")
    if not choco:
        return False
    if _run_install([choco, "install", "tesseract", "-y", "--no-progress"]):
        logger.info("Installed Tesseract via Chocolatey.")
        return True
    return False


def _try_scoop() -> bool:
    scoop = shutil.which("scoop")
    if not scoop:
        return False
    if _run_install([scoop, "install", "tesseract", "-q"]):
        logger.info("Installed Tesseract via Scoop.")
        return True
    return False


def _try_install_windows() -> bool:
    return _try_winget() or _try_choco() or _try_scoop()


def ensure_tesseract_windows(config: OCRConfig) -> bool:
    """
    On Windows: if Tesseract executable is missing, attempt a silent install once per process.

    Sets ``config.tesseract_cmd`` when a working binary is found.
    Set ``OCR_AUTO_INSTALL_TESSERACT=0`` to skip auto-install (detection only).

    Returns True if pytesseract can run ``get_tesseract_version()`` after this call.
    """
    if sys.platform != "win32":
        exe = _resolve_tesseract_exe(config.tesseract_cmd)
        if exe:
            config.tesseract_cmd = exe
        return _pytesseract_ok(config.tesseract_cmd)

    if os.getenv("OCR_AUTO_INSTALL_TESSERACT", "1").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
    ):
        exe = _resolve_tesseract_exe(config.tesseract_cmd)
        if exe:
            config.tesseract_cmd = exe
        return _pytesseract_ok(config.tesseract_cmd)

    global _install_attempted

    exe = _resolve_tesseract_exe(config.tesseract_cmd)
    if exe and _pytesseract_ok(exe):
        config.tesseract_cmd = exe
        return True

    if _install_attempted:
        return False
    _install_attempted = True

    logger.info("Tesseract not found; attempting silent install (winget / choco / scoop)...")
    if not _try_install_windows():
        logger.warning(
            "Tesseract auto-install did not complete. Install manually or add TESSERACT_CMD."
        )
        return False

    # Refresh path after installer (common location first)
    for p in _WIN_TESSERACT_PATHS:
        if os.path.isfile(p) and _pytesseract_ok(p):
            config.tesseract_cmd = p
            logger.info("Tesseract ready at %s", p)
            return True

    w = shutil.which("tesseract")
    if w and _pytesseract_ok(w):
        config.tesseract_cmd = w
        logger.info("Tesseract ready at %s", w)
        return True

    logger.warning("Tesseract install reported success but executable not found in expected paths.")
    return False
