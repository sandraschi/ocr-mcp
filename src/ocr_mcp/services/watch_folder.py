import asyncio
import logging
import shutil
import time
from pathlib import Path
from typing import List, Set

from ocr_mcp.core.backend_manager import BackendManager
from ocr_mcp.core.config import config
from ocr_mcp.tools._workflow import workflow_management

logger = logging.getLogger(__name__)


class WatchFolderService:
    """
    Watches a folder for new documents and automatically processes them using the OCR workflow.
    """

    def __init__(self, backend_manager: BackendManager):
        self.backend_manager = backend_manager
        self.is_running = False
        self._processed_files: Set[str] = set()

    async def start(self):
        """Start the watch folder service loop."""
        if not config.watch_folder_enabled:
            logger.info("Watch folder service disabled in config")
            return

        if not config.watch_folder_path or not config.watch_folder_path.exists():
            logger.error(f"Watch folder path invalid: {config.watch_folder_path}")
            return

        # Ensure output directories exist
        processed_dir = config.watch_folder_path / "processed"
        failed_dir = config.watch_folder_path / "failed"
        output_dir = config.watch_folder_output_path or (
            config.watch_folder_path / "output"
        )

        processed_dir.mkdir(exist_ok=True)
        failed_dir.mkdir(exist_ok=True)
        output_dir.mkdir(exist_ok=True)

        self.is_running = True
        logger.info(f"Watch folder service started on: {config.watch_folder_path}")
        logger.info(f"Output directory: {output_dir}")

        while self.is_running:
            try:
                await self._scan_and_process(processed_dir, failed_dir, output_dir)
            except Exception as e:
                logger.error(f"Error in watch folder loop: {e}")

            await asyncio.sleep(config.watch_folder_interval)

    def stop(self):
        """Stop the watch folder service."""
        logger.info("Stopping watch folder service...")
        self.is_running = False

    async def _scan_and_process(
        self, processed_dir: Path, failed_dir: Path, output_dir: Path
    ):
        """Scan for new files and process them."""
        # Find new files (excluding subdirectories)
        files_to_process = [
            f
            for f in config.watch_folder_path.iterdir()
            if f.is_file()
            and f.name not in self._processed_files
            and not f.name.startswith(".")
        ]

        if not files_to_process:
            return

        logger.info(f"Found {len(files_to_process)} new files to process")

        # Process in batches using intelligent workflow
        # Convert Path objects to strings for the tool
        file_paths = [str(f) for f in files_to_process]

        # Use the intelligent batch workflow we implemented
        result = await workflow_management(
            operation="process_batch_intelligent",
            backend_manager=self.backend_manager,
            document_paths=file_paths,
            workflow_type="auto",
            output_directory=str(output_dir),
            save_intermediates=False,
        )

        # Handle file movements based on results
        results_map = {
            r["document_path"]: r.get("success", False)
            for r in result.get("results", [])
        }

        for file_path in files_to_process:
            success = results_map.get(str(file_path), False)
            dest_dir = processed_dir if success else failed_dir

            try:
                # Move file to appropriate directory
                shutil.move(str(file_path), str(dest_dir / file_path.name))
                logger.info(f"Moved {file_path.name} to {dest_dir.name}")
            except Exception as e:
                logger.error(f"Failed to move file {file_path}: {e}")
