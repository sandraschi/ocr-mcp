#!/usr/bin/env python3
"""
Run the OCR-MCP WebApp
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from webapp.backend.app import main

if __name__ == "__main__":
    print("🚀 Starting OCR-MCP WebApp...")
    print("📱 Web interface will be available at: http://localhost:8000")
    print("❌ Press Ctrl+C to stop the server")
    print()

    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 OCR-MCP WebApp stopped")
    except Exception as e:
        print(f"❌ Error starting webapp: {e}")
        sys.exit(1)
