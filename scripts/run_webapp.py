import logging

logger = logging.getLogger(__name__)
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

from backend.app import main

if __name__ == "__main__":
    port = os.getenv("WEBAPP_PORT", "15000")
    logger.info("STARTING OCR-MCP WebApp...")
    logger.info(f"Web interface will be available at: http://localhost:{port}")
    logger.info("Press Ctrl+C to stop the server")

    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nOCR-MCP WebApp stopped")
    except Exception as e:
        logger.info(f"ERROR starting webapp: {e}")
        sys.exit(1)
