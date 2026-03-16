import logging
import sys
from pathlib import Path

# Add src to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from ocr_mcp.backends.scanner.wia_scanner import WIABackend

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

    def main():
        logger.info("Starting Scanner Hardware Verification...")

        backend = WIABackend()
        if not backend.is_available():
            logger.error(
                "WIA Backend is NOT available. This normally means comtypes or pythoncom is missing, or you are not on Windows."
            )
            return

        logger.info("WIA Backend initialized successfully.")

        logger.info("Performing scanner discovery...")
        scanners = backend.discover_scanners()

        if not scanners:
            logger.warning("No scanners discovered.")
            logger.info("Checking diagnostics...")
            diag = backend.get_diagnostics()
            for k, v in diag.items():
                logger.info(f"  {k}: {v}")
        else:
            logger.info(f"Discovered {len(scanners)} scanner(s).")
            for i, s in enumerate(scanners):
                logger.info(f"[{i}] Name: {s.name} (ID: {s.device_id})")

            # Try to scan with the first scanner
            target_id = scanners[0].device_id
            from ocr_mcp.backends.scanner.wia_scanner import ScanSettings

            settings = ScanSettings(dpi=150, color_mode="Grayscale")

            logger.info(f"Attempting test scan on {target_id}...")
            image = backend.scan_document(target_id.replace("wia:", ""), settings)

            if image:
                logger.info(f"SUCCESS! Scan completed. Size: {image.size}")
                # Save locally for verification
                image.save("test_scan_result.png")
                logger.info("Saved test_scan_result.png")
            else:
                logger.error("Scan FAILED. Check backend logs for WIA errors.")

except ImportError as e:
    print(f"Import Error: {e}")
    print(
        "Ensure you are running this from the project root or in an environment where ocr_mcp is visible."
    )
except Exception as e:
    print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    if "main" in globals():
        main()
    else:
        print("Script failed to initialize 'main' function.")
