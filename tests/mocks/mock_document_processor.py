"""
Mock Document Processor Implementation

Mock implementation for document processing functionality
to enable testing without requiring actual file I/O operations.
"""

import tempfile
from pathlib import Path
from typing import List, Dict, Any, Union
from PIL import Image


class MockDocumentProcessor:
    """Mock document processor for testing."""

    def __init__(self):
        self._available = True
        self.call_count = 0
        self.last_call_args = None
        self.temp_files_created = []
        self.extracted_images = []

    def is_available(self) -> bool:
        return self._available

    def detect_file_type(self, file_path: Union[str, Path]) -> str:
        """Mock file type detection."""
        self.call_count += 1
        file_path = Path(file_path)

        # Determine type based on file extension
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return "pdf"
        elif suffix == ".cbz":
            return "cbz"
        elif suffix == ".cbr":
            return "cbr"
        elif suffix in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            return "image"
        else:
            return "unknown"

    def extract_images(self, file_path: Union[str, Path], **kwargs) -> List[Dict[str, Any]]:
        """Mock image extraction from documents."""
        self.call_count += 1
        self.last_call_args = (file_path, kwargs)
        file_path = Path(file_path)

        file_type = self.detect_file_type(file_path)

        if file_type == "pdf":
            return self._mock_extract_pdf_images(file_path, **kwargs)
        elif file_type == "cbz":
            return self._mock_extract_cbz_images(file_path, **kwargs)
        elif file_type == "cbr":
            return self._mock_extract_cbr_images(file_path, **kwargs)
        elif file_type == "image":
            return self._mock_extract_single_image(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _mock_extract_pdf_images(self, pdf_path: Path, dpi: int = 300, **kwargs) -> List[Dict[str, Any]]:
        """Mock PDF image extraction."""
        # Create mock images
        temp_dir = Path(tempfile.mkdtemp())
        images_info = []

        # Simulate 3 pages
        for page_num in range(3):
            # Create mock image
            mock_image = Image.new('RGB', (1000, 1500), color='white')

            # Save to temp file
            image_filename = "04d"
            image_path = temp_dir / image_filename
            mock_image.save(image_path)
            self.temp_files_created.append(image_path)

            metadata = {
                "width": 1000,
                "height": 1500,
                "dpi": dpi,
                "format": "PNG",
                "mode": "RGB",
                "source_type": "pdf",
                "total_pages": 3
            }

            images_info.append({
                "image_path": str(image_path),
                "page_number": page_num,
                "metadata": metadata
            })

        self.extracted_images.extend(images_info)
        return images_info

    def _mock_extract_cbz_images(self, cbz_path: Path, **kwargs) -> List[Dict[str, Any]]:
        """Mock CBZ image extraction."""
        temp_dir = Path(tempfile.mkdtemp())
        images_info = []

        # Simulate comic pages
        for page_num in range(5):
            mock_image = Image.new('RGB', (800, 1200), color='white')
            image_filename = f"comic_page_{page_num:03d}.png"
            image_path = temp_dir / image_filename
            mock_image.save(image_path)
            self.temp_files_created.append(image_path)

            metadata = {
                "width": 800,
                "height": 1200,
                "format": "PNG",
                "mode": "RGB",
                "source_type": "cbz",
                "archive_path": f"page_{page_num:03d}.jpg",
                "total_pages": 5
            }

            images_info.append({
                "image_path": str(image_path),
                "page_number": page_num,
                "metadata": metadata
            })

        self.extracted_images.extend(images_info)
        return images_info

    def _mock_extract_cbr_images(self, cbr_path: Path, **kwargs) -> List[Dict[str, Any]]:
        """Mock CBR image extraction."""
        temp_dir = Path(tempfile.mkdtemp())
        images_info = []

        # Simulate RAR comic pages
        for page_num in range(4):
            mock_image = Image.new('RGB', (900, 1300), color='white')
            image_filename = f"rar_page_{page_num:03d}.png"
            image_path = temp_dir / image_filename
            mock_image.save(image_path)
            self.temp_files_created.append(image_path)

            metadata = {
                "width": 900,
                "height": 1300,
                "format": "PNG",
                "mode": "RGB",
                "source_type": "cbr",
                "archive_path": f"page_{page_num:03d}.jpg",
                "total_pages": 4
            }

            images_info.append({
                "image_path": str(image_path),
                "page_number": page_num,
                "metadata": metadata
            })

        self.extracted_images.extend(images_info)
        return images_info

    def _mock_extract_single_image(self, image_path: Path, **kwargs) -> List[Dict[str, Any]]:
        """Mock single image handling."""
        # For single images, just return the image info
        try:
            with Image.open(image_path) as img:
                metadata = {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format or "PNG",
                    "mode": img.mode,
                    "source_type": "image",
                    "total_pages": 1
                }
        except Exception:
            # If we can't open the image, create mock metadata
            metadata = {
                "width": 1000,
                "height": 1000,
                "format": "PNG",
                "mode": "RGB",
                "source_type": "image",
                "total_pages": 1
            }

        return [{
            "image_path": str(image_path),
            "page_number": 0,
            "metadata": metadata
        }]

    def cleanup_temp_files(self):
        """Mock cleanup of temporary files."""
        self.call_count += 1
        # In real implementation, this would delete temp files
        # For testing, we just track the call
        temp_files_count = len(self.temp_files_created)
        self.temp_files_created.clear()
        return temp_files_count


# Factory functions
def create_mock_document_processor() -> MockDocumentProcessor:
    """Factory for document processor mock."""
    return MockDocumentProcessor()


# Test data generators
def generate_mock_pdf_metadata(
    pages: int = 3,
    dpi: int = 300,
    width: int = 1000,
    height: int = 1500
) -> List[Dict[str, Any]]:
    """Generate mock PDF extraction metadata."""
    images_info = []
    for page_num in range(pages):
        metadata = {
            "width": width,
            "height": height,
            "dpi": dpi,
            "format": "PNG",
            "mode": "RGB",
            "source_type": "pdf",
            "total_pages": pages
        }

        images_info.append({
            "image_path": f"/tmp/pdf_page_{page_num:04d}.png",
            "page_number": page_num,
            "metadata": metadata
        })

    return images_info


def generate_mock_cbz_metadata(
    pages: int = 5,
    width: int = 800,
    height: int = 1200
) -> List[Dict[str, Any]]:
    """Generate mock CBZ extraction metadata."""
    images_info = []
    for page_num in range(pages):
        metadata = {
            "width": width,
            "height": height,
            "format": "PNG",
            "mode": "RGB",
            "source_type": "cbz",
            "archive_path": f"page_{page_num:03d}.jpg",
            "total_pages": pages
        }

        images_info.append({
            "image_path": f"/tmp/comic_page_{page_num:03d}.png",
            "page_number": page_num,
            "metadata": metadata
        })

    return images_info


def create_mock_image_file(
    temp_dir: Path,
    filename: str = "test.png",
    width: int = 100,
    height: int = 100,
    color: str = 'white'
) -> Path:
    """Create a mock image file for testing."""
    image_path = temp_dir / filename
    image = Image.new('RGB', (width, height), color=color)
    image.save(image_path)
    return image_path


def create_mock_pdf_file(temp_dir: Path, filename: str = "test.pdf", pages: int = 1) -> Path:
    """Create a mock PDF file for testing."""
    pdf_path = temp_dir / filename
    # In a real implementation, this would create an actual PDF
    # For testing, we just create a file with PDF-like content
    pdf_path.write_text(f"%PDF-1.4\n%Mock PDF with {pages} pages\n%%EOF")
    return pdf_path


def create_mock_cbz_file(temp_dir: Path, filename: str = "test.cbz", pages: int = 3) -> Path:
    """Create a mock CBZ file for testing."""
    cbz_path = temp_dir / filename
    # In a real implementation, this would create an actual CBZ archive
    # For testing, we just create a file with CBZ-like content
    cbz_path.write_text(f"Mock CBZ archive with {pages} pages")
    return cbz_path






