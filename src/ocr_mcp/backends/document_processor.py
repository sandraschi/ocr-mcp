"""
Document Processing Backend for OCR-MCP

Handles various document formats and extracts images for OCR processing:
- PDF files (raster PDFs, scans, mixed content)
- CBZ/CBR comic book archives (ZIP/RAR containers of images)
- Direct image files (JPG, PNG, TIFF, BMP, etc.)
- Multi-page documents and batch processing
- Advanced manga/comic processing modes
"""

import logging
import zipfile
import rarfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import tempfile
import shutil

logger = logging.getLogger(__name__)

# Optional imports - handle gracefully if not available
try:
    from PIL import Image
    import fitz  # PyMuPDF for PDF processing
    PIL_AVAILABLE = True
    PYMUPDF_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Document processing dependencies not available: {e}")
    PIL_AVAILABLE = False
    PYMUPDF_AVAILABLE = False
    Image = None
    fitz = None


class DocumentProcessor:
    """
    Processes various document formats and extracts images for OCR.

    Supports advanced document processing including:
    - PDF rasterization and image extraction
    - Comic book archive processing (CBZ/CBR)
    - Manga-specific layout analysis
    - Multi-page document handling
    """

    def __init__(self):
        if not PIL_AVAILABLE or not PYMUPDF_AVAILABLE:
            logger.warning("Document processing unavailable - missing dependencies")
            self._available = False
        else:
            self._available = True

        # Temporary directory for extracted images
        self._temp_dir = None

    def is_available(self) -> bool:
        """Check if document processing is available."""
        return self._available

    def detect_file_type(self, file_path: Union[str, Path]) -> str:
        """
        Detect the file type and processing requirements.

        Returns:
            File type: "pdf", "cbz", "cbr", "image", "unknown"
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return "unknown"

        # Check file extension first
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return "pdf"
        elif suffix == ".cbz":
            return "cbz"
        elif suffix == ".cbr":
            return "cbr"
        elif suffix in [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif", ".webp"]:
            return "image"
        else:
            # Try to detect by content
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(8)

                # PDF detection
                if header.startswith(b'%PDF'):
                    return "pdf"

                # ZIP detection (CBZ)
                if header.startswith(b'PK\x03\x04'):
                    return "cbz"

                # RAR detection (CBR) - RAR signature
                if header.startswith(b'Rar!\x1a\x07'):
                    return "cbr"

                # Try image detection with PIL
                if PIL_AVAILABLE:
                    try:
                        with Image.open(file_path) as img:
                            return "image"
                    except:
                        pass

            except Exception as e:
                logger.debug(f"File type detection failed for {file_path}: {e}")

        return "unknown"

    def extract_images(self, file_path: Union[str, Path], **kwargs) -> List[Dict[str, Any]]:
        """
        Extract images from various document formats.

        Returns a list of image info dictionaries containing:
        - image_path: Path to extracted image
        - page_number: Page/document number (0-based)
        - metadata: Additional information (dimensions, DPI, etc.)
        """
        file_path = Path(file_path)
        file_type = self.detect_file_type(file_path)

        logger.info(f"Processing {file_type} file: {file_path}")

        if file_type == "pdf":
            return self._extract_pdf_images(file_path, **kwargs)
        elif file_type == "cbz":
            return self._extract_cbz_images(file_path, **kwargs)
        elif file_type == "cbr":
            return self._extract_cbr_images(file_path, **kwargs)
        elif file_type == "image":
            return self._extract_single_image(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _extract_pdf_images(self, pdf_path: Path, dpi: int = 300, **kwargs) -> List[Dict[str, Any]]:
        """Extract images from PDF file."""
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF not available for PDF processing")

        images_info = []

        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(str(pdf_path))

            # Create temporary directory for extracted images
            temp_dir = self._get_temp_dir()

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Convert page to image
                pix = page.get_pixmap(dpi=dpi)

                # Save as PNG
                image_filename = f"pdf_page_{page_num:04d}.png"
                image_path = temp_dir / image_filename

                pix.save(str(image_path))

                # Get page metadata
                metadata = {
                    "width": pix.width,
                    "height": pix.height,
                    "dpi": dpi,
                    "colorspace": pix.colorspace,
                    "source_type": "pdf",
                    "total_pages": len(doc)
                }

                images_info.append({
                    "image_path": str(image_path),
                    "page_number": page_num,
                    "metadata": metadata
                })

            doc.close()
            logger.info(f"Extracted {len(images_info)} images from PDF")

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise

        return images_info

    def _extract_cbz_images(self, cbz_path: Path, **kwargs) -> List[Dict[str, Any]]:
        """Extract images from CBZ (ZIP) comic archive."""
        images_info = []

        try:
            temp_dir = self._get_temp_dir()

            with zipfile.ZipFile(cbz_path, 'r') as zip_ref:
                # Get list of image files (common comic image formats)
                image_files = []
                for file_info in zip_ref.filelist:
                    if self._is_image_file(file_info.filename):
                        image_files.append(file_info)

                # Sort by filename for proper page order
                image_files.sort(key=lambda x: x.filename)

                for page_num, file_info in enumerate(image_files):
                    try:
                        # Extract image
                        zip_ref.extract(file_info, temp_dir)
                        extracted_path = temp_dir / file_info.filename

                        # Get image metadata
                        if PIL_AVAILABLE:
                            with Image.open(extracted_path) as img:
                                metadata = {
                                    "width": img.width,
                                    "height": img.height,
                                    "format": img.format,
                                    "mode": img.mode,
                                    "source_type": "cbz",
                                    "archive_path": file_info.filename,
                                    "total_pages": len(image_files)
                                }
                        else:
                            metadata = {
                                "source_type": "cbz",
                                "archive_path": file_info.filename,
                                "total_pages": len(image_files)
                            }

                        images_info.append({
                            "image_path": str(extracted_path),
                            "page_number": page_num,
                            "metadata": metadata
                        })

                    except Exception as e:
                        logger.warning(f"Failed to extract {file_info.filename}: {e}")
                        continue

            logger.info(f"Extracted {len(images_info)} images from CBZ")

        except Exception as e:
            logger.error(f"CBZ extraction failed: {e}")
            raise

        return images_info

    def _extract_cbr_images(self, cbr_path: Path, **kwargs) -> List[Dict[str, Any]]:
        """Extract images from CBR (RAR) comic archive."""
        images_info = []

        try:
            # Check if rarfile is available
            if not hasattr(rarfile, 'RarFile'):
                raise ImportError("rarfile library not available for CBR processing")

            temp_dir = self._get_temp_dir()

            with rarfile.RarFile(cbr_path, 'r') as rar_ref:
                # Get list of image files
                image_files = []
                for file_info in rar_ref.filelist:
                    if hasattr(file_info, 'filename') and self._is_image_file(file_info.filename):
                        image_files.append(file_info)

                # Sort by filename
                image_files.sort(key=lambda x: x.filename)

                for page_num, file_info in enumerate(image_files):
                    try:
                        # Extract image
                        rar_ref.extract(file_info, temp_dir)
                        extracted_path = temp_dir / file_info.filename

                        # Get image metadata
                        if PIL_AVAILABLE:
                            with Image.open(extracted_path) as img:
                                metadata = {
                                    "width": img.width,
                                    "height": img.height,
                                    "format": img.format,
                                    "mode": img.mode,
                                    "source_type": "cbr",
                                    "archive_path": file_info.filename,
                                    "total_pages": len(image_files)
                                }
                        else:
                            metadata = {
                                "source_type": "cbr",
                                "archive_path": file_info.filename,
                                "total_pages": len(image_files)
                            }

                        images_info.append({
                            "image_path": str(extracted_path),
                            "page_number": page_num,
                            "metadata": metadata
                        })

                    except Exception as e:
                        logger.warning(f"Failed to extract {file_info.filename}: {e}")
                        continue

            logger.info(f"Extracted {len(images_info)} images from CBR")

        except Exception as e:
            logger.error(f"CBR extraction failed: {e}")
            raise

        return images_info

    def _extract_single_image(self, image_path: Path, **kwargs) -> List[Dict[str, Any]]:
        """Handle single image files."""
        if not PIL_AVAILABLE:
            raise ImportError("PIL not available for image processing")

        try:
            with Image.open(image_path) as img:
                metadata = {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "source_type": "image",
                    "total_pages": 1
                }

            return [{
                "image_path": str(image_path),
                "page_number": 0,
                "metadata": metadata
            }]

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise

    def _is_image_file(self, filename: str) -> bool:
        """Check if file is an image based on extension."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp'}
        return Path(filename).suffix.lower() in image_extensions

    def _get_temp_dir(self) -> Path:
        """Get or create temporary directory for extracted images."""
        if self._temp_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="ocr_mcp_"))
        return self._temp_dir

    def cleanup_temp_files(self):
        """Clean up temporary extracted files."""
        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
                self._temp_dir = None
                logger.debug("Cleaned up temporary files")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp files: {e}")

    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup_temp_files()


# Global document processor instance
document_processor = DocumentProcessor()
