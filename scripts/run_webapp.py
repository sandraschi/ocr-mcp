#!/usr/bin/env python3
"""
Run the OCR-MCP WebApp
"""

import sys
import os
from pathlib import Path

# Add the project root and src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from webapp.backend.app import main

if __name__ == "__main__":
    port = os.getenv("WEBAPP_PORT", "7460")
    print("STARTING OCR-MCP WebApp...")
    print(f"Web interface will be available at: http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    print()

    try:
        main()
    except KeyboardInterrupt:
        print("\nOCR-MCP WebApp stopped")
    except Exception as e:
        print(f"ERROR starting webapp: {e}")
        sys.exit(1)
