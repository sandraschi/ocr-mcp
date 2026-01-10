import logging
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
OCR-MCP MCPB Package Builder

Builds OCR-MCP as an MCPB package for easy distribution and installation.
"""

import argparse
import shutil
import subprocess
from pathlib import Path


def get_version() -> str:
    """Get version from pyproject.toml"""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        import re
        content = pyproject_path.read_text()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    return "1.0.0"


def build_mcpb_package(
    output_dir: Path,
    version: str,
    include_models: bool = False,
    compress: bool = False
) -> Path:
    """Build the MCPB package"""

    logger.info("Building OCR-MCP MCPB Package...")
    logger.info(f"Output Directory: {output_dir}")
    logger.info(f"Package Version: {version}")

    # Package directory
    package_name = "ocr-mcp"
    package_dir = output_dir / f"{package_name}-{version}"
    mcpb_dir = package_dir / "mcpb"

    # Clean previous build
    if package_dir.exists():
        shutil.rmtree(package_dir)

    # Create package structure
    logger.info("Creating package structure...")
    mcpb_dir.mkdir(parents=True)
    (mcpb_dir / "src").mkdir()
    (mcpb_dir / "assets" / "prompts").mkdir(parents=True)

    project_root = Path(__file__).parent.parent

    # Copy MCPB files
    logger.info("Copying MCPB manifest and assets...")
    shutil.copy(project_root / "mcp-server" / "manifest.json", mcpb_dir)
    shutil.copytree(
        project_root / "mcp-server" / "assets",
        mcpb_dir / "assets",
        dirs_exist_ok=True
    )

    # Copy source code
    logger.info("Copying source code...")
    shutil.copytree(
        project_root / "src",
        mcpb_dir / "src",
        dirs_exist_ok=True
    )

    # Copy Python files
    logger.info("Copying Python dependencies...")
    shutil.copy(project_root / "pyproject.toml", package_dir)
    shutil.copy(project_root / "requirements.txt", package_dir)

    # Create installation script
    install_script = '''#!/usr/bin/env bash
#
# OCR-MCP Installation Script
#
# This script installs OCR-MCP as an MCP server.
#

set -e

INSTALL_DIR="${HOME}/.mcp/servers/ocr-mcp"
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Installing OCR-MCP..."

# Check if already installed
if [[ -d "$INSTALL_DIR" && "$FORCE" != true ]]; then
    echo "OCR-MCP is already installed at: $INSTALL_DIR"
    echo "Use --force to reinstall"
    exit 0
fi

# Create installation directory
if [[ -d "$INSTALL_DIR" ]]; then
    rm -rf "$INSTALL_DIR"
fi
mkdir -p "$INSTALL_DIR"

# Copy files
echo "Copying files..."
cp -r mcpb/* "$INSTALL_DIR/"
cp pyproject.toml "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"

# Install dependencies
echo "Installing Python dependencies..."
cd "$INSTALL_DIR"
python -m pip install -e .

echo "OCR-MCP installed successfully!"
echo "Installation directory: $INSTALL_DIR"
'''

    (package_dir / "install.sh").write_text(install_script)
    (package_dir / "install.sh").chmod(0o755)

    # Create Windows batch file
    install_batch = '''@echo off
REM OCR-MCP Installation Script for Windows
REM
REM This script installs OCR-MCP as an MCP server.

setlocal

set "INSTALL_DIR=%USERPROFILE%\\.mcp\\servers\\ocr-mcp"
set "FORCE=false"

:parse_args
if "%1"=="" goto :end_parse
if "%1"=="--install-dir" (
    set "INSTALL_DIR=%2"
    shift & shift
    goto :parse_args
)
if "%1"=="--force" (
    set "FORCE=true"
    shift
    goto :parse_args
)
echo Unknown option: %1
exit /b 1

:end_parse

echo Installing OCR-MCP...

REM Check if already installed
if exist "%INSTALL_DIR%" if "%FORCE%"=="false" (
    echo OCR-MCP is already installed at: %INSTALL_DIR%
    echo Use --force to reinstall
    exit /b 0
)

REM Create installation directory
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"
mkdir "%INSTALL_DIR%" 2>nul

REM Copy files
echo Copying files...
xcopy /e /i /y "mcpb\\*" "%INSTALL_DIR%\\" >nul
copy "pyproject.toml" "%INSTALL_DIR%\\" >nul
copy "requirements.txt" "%INSTALL_DIR%\\" >nul

REM Install dependencies
echo Installing Python dependencies...
cd /d "%INSTALL_DIR%"
python -m pip install -e .

echo OCR-MCP installed successfully!
echo Installation directory: %INSTALL_DIR%

endlocal
'''

    (package_dir / "install.bat").write_text(install_batch)

    # Create README for package
    package_readme = f'''# OCR-MCP v{version}

Professional Document Processing Suite with 7 State-of-the-Art OCR Engines.

## Installation

### Linux/macOS
Run the installation script:
```bash
./install.sh
```

### Windows
Run the batch file:
```cmd
install.bat
```

Or install manually:
```bash
pip install -e .
```

## Configuration

Add to your `claude_desktop_config.json`:

```json
{{
  "mcpServers": {{
    "ocr-mcp": {{
      "command": "python",
      "args": ["-m", "ocr_mcp.server"]
    }}
  }}
}}
```

## Features

- 7 Advanced OCR Backends (Mistral OCR 3, DeepSeek-OCR, Florence-2, DOTS.OCR, PP-OCRv5, Qwen-Image-Layered, Tesseract)
- Direct Scanner Integration (WIA/TWAIN)
- Document Processing (PDF, CBZ, Images)
- Batch Processing with Progress Tracking
- Quality Assessment and Backend Comparison
- Web Interface for Professional Workflows

For full documentation, visit: https://github.com/sandraschi/ocr-mcp
'''

    (package_dir / "README.md").write_text(package_readme)

    # Optional: Include models (significantly increases package size)
    if include_models:
        logger.info("Including pre-downloaded models...")
        # This would require downloading models, which is complex
        # For now, just note it in the manifest

    # Create compressed archive if requested
    if compress:
        logger.info("Creating compressed package...")
        archive_name = f"{package_name}-{version}.mcpb"
        archive_path = output_dir / archive_name

        try:
            # Try using tar (Linux/macOS)
            subprocess.run([
                "tar", "czf", str(archive_path), "-C", str(output_dir), f"{package_name}-{version}"
            ], check=True)
            logger.info(f"Created compressed package: {archive_path}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Try using zip
                subprocess.run([
                    "zip", "-r", str(archive_path), f"{package_name}-{version}"
                ], cwd=output_dir, check=True)
                logger.info(f"Created compressed package: {archive_path}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.info("Warning: Could not create compressed archive. tar/zip not available.")

    logger.info("SUCCESS: OCR-MCP MCPB package created successfully!")
    logger.info(f"Package location: {package_dir}")

    if compress:
        logger.info(f"Compressed archive: {output_dir / f'{package_name}-{version}.mcpb'}")

    logger.info()
    logger.info("To install on another system:")
    logger.info("1. Copy the package directory to the target system")
    logger.info("2. Run: ./install.sh (Linux/macOS) or install.bat (Windows)")
    logger.info("3. Add to claude_desktop_config.json")

    return package_dir


def main():
    parser = argparse.ArgumentParser(description="Build OCR-MCP MCPB package")
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("dist"),
        help="Output directory for the MCPB package"
    )
    parser.add_argument(
        "--version", "-v",
        help="Package version (default: from pyproject.toml)"
    )
    parser.add_argument(
        "--include-models",
        action="store_true",
        help="Include pre-downloaded models in package (increases size)"
    )
    parser.add_argument(
        "--compress", "-c",
        action="store_true",
        help="Create compressed .mcpb archive"
    )

    args = parser.parse_args()

    # Get version
    version = args.version or get_version()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Build package
    build_mcpb_package(
        output_dir=args.output_dir,
        version=version,
        include_models=args.include_models,
        compress=args.compress
    )


if __name__ == "__main__":
    main()