import logging

logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
Run the OCR-MCP WebApp
"""

import os
import sys
from pathlib import Path

# Add the project root and src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from backend.app import main

if __name__ == "__main__":
    port = os.getenv("WEBAPP_PORT", "15550")
    logger.info("STARTING OCR-MCP WebApp...")
    logger.info(f"Web interface will be available at: http://localhost:{port}")
    logger.info("Press Ctrl+C to stop the server")

    try:
        # Pre-download models if needed
        logger.info("Initializing model storage...")
        try:
            from scripts.download_models import download_models

            download_models()
        except ImportError:
            # Fallback if scripts module generic import fails, though sys.path should handle it
            # Or if dependencies missing (shouldn't happen in container)
            logger.warning("Could not import download_models script, skipping pre-download.")
        except Exception as e:
            logger.error(f"Error during model pre-download: {e}")
            # We continue even if download fails, app might still work or will fail later on specific requests

        main()
    except KeyboardInterrupt:
        logger.info("\nOCR-MCP WebApp stopped")
    except Exception as e:
        logger.error(f"ERROR starting webapp: {e}")
        sys.exit(1)
