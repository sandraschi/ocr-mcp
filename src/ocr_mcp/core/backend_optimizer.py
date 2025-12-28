"""
OCR-MCP Backend Optimizer: Intelligent backend selection based on document characteristics

Analyzes document properties and automatically selects the optimal OCR backend for maximum accuracy.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
from enum import Enum

from PIL import Image
import cv2
import numpy as np

from .config import OCRConfig

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Document type classifications"""
    PRINTED_TEXT = "printed_text"           # Clean printed documents
    HANDWRITING = "handwriting"             # Handwritten text
    SCANNED_DOCUMENT = "scanned_document"   # Scanned pages
    RECEIPT = "receipt"                     # Receipts/invoices
    FORM = "form"                           # Forms with fields
    TABLE = "table"                         # Documents with tables
    MIXED_CONTENT = "mixed_content"         # Text + images/graphics
    MATHEMATICAL = "mathematical"           # Mathematical formulas
    COMIC = "comic"                         # Comic books/manga
    MULTILINGUAL = "multilingual"           # Multiple languages
    HISTORICAL = "historical"               # Old/archival documents


class ContentComplexity(Enum):
    """Content complexity levels"""
    SIMPLE = "simple"       # Clean text, few characters
    MODERATE = "moderate"   # Standard documents
    COMPLEX = "complex"     # Dense text, mixed content
    VERY_COMPLEX = "very_complex"  # Mathematical, tables, complex layouts


class ImageQuality(Enum):
    """Image quality assessments"""
    EXCELLENT = "excellent"  # High DPI, clean scan
    GOOD = "good"           # Standard quality
    FAIR = "fair"           # Some noise/artifacts
    POOR = "poor"           # Low quality, heavy artifacts
    VERY_POOR = "very_poor" # Severely degraded


class DocumentAnalyzer:
    """Analyzes document characteristics for optimal backend selection"""

    def __init__(self, config: OCRConfig):
        self.config = config

    def analyze_document(self, image_path: Path) -> Dict[str, Any]:
        """
        Comprehensive document analysis for backend optimization

        Returns detailed analysis including:
        - Document type classification
        - Content complexity
        - Image quality assessment
        - Language detection
        - Layout characteristics
        - Optimal backend recommendations
        """
        try:
            # Open image and get basic properties
            with Image.open(image_path) as img:
                width, height = img.size
                mode = img.mode
                # Convert to RGB if needed for analysis
                if mode not in ['RGB', 'L']:
                    img = img.convert('RGB')

            # Convert to numpy array for OpenCV analysis
            cv_image = cv2.imread(str(image_path))
            if cv_image is None:
                raise ValueError(f"Could not load image: {image_path}")

            # Perform comprehensive analysis
            analysis = {
                "dimensions": {"width": width, "height": height},
                "aspect_ratio": width / height if height > 0 else 0,
                "document_type": self._classify_document_type(cv_image),
                "content_complexity": self._assess_content_complexity(cv_image),
                "image_quality": self._assess_image_quality(cv_image),
                "layout_characteristics": self._analyze_layout(cv_image),
                "estimated_language": self._detect_language(cv_image),
                "backend_recommendations": []
            }

            # Generate backend recommendations
            analysis["backend_recommendations"] = self._generate_backend_recommendations(analysis)

            logger.info(f"Document analysis complete for {image_path.name}: {analysis['document_type'].value}")
            return analysis

        except Exception as e:
            logger.error(f"Document analysis failed for {image_path}: {e}")
            # Return fallback analysis
            return {
                "dimensions": {"width": 0, "height": 0},
                "document_type": DocumentType.PRINTED_TEXT,
                "content_complexity": ContentComplexity.MODERATE,
                "image_quality": ImageQuality.GOOD,
                "layout_characteristics": {"has_tables": False, "has_forms": False, "text_density": 0.5},
                "estimated_language": "en",
                "backend_recommendations": ["auto"],
                "error": str(e)
            }

    def _classify_document_type(self, image: np.ndarray) -> DocumentType:
        """Classify document type based on visual characteristics"""

        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        # Calculate various metrics
        text_density = self._calculate_text_density(gray)
        has_tables = self._detect_tables(gray)
        has_forms = self._detect_forms(gray)
        color_variance = self._calculate_color_variance(image)
        has_mathematical = self._detect_mathematical_symbols(gray)

        # Document type classification logic
        if has_mathematical and text_density > 0.3:
            return DocumentType.MATHEMATICAL
        elif has_tables and text_density > 0.4:
            return DocumentType.TABLE
        elif has_forms:
            return DocumentType.FORM
        elif color_variance > 1000 and text_density < 0.2:
            return DocumentType.COMIC
        elif text_density > 0.5 and self._detect_receipt_patterns(gray):
            return DocumentType.RECEIPT
        elif self._detect_handwriting(gray):
            return DocumentType.HANDWRITING
        elif text_density > 0.6:
            return DocumentType.MIXED_CONTENT
        elif self._detect_scanned_artifacts(gray):
            return DocumentType.SCANNED_DOCUMENT
        else:
            return DocumentType.PRINTED_TEXT

    def _assess_content_complexity(self, image: np.ndarray) -> ContentComplexity:
        """Assess content complexity based on text density and layout"""

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        text_density = self._calculate_text_density(gray)
        layout_complexity = self._calculate_layout_complexity(gray)

        complexity_score = (text_density * 0.6) + (layout_complexity * 0.4)

        if complexity_score > 0.7:
            return ContentComplexity.VERY_COMPLEX
        elif complexity_score > 0.5:
            return ContentComplexity.COMPLEX
        elif complexity_score > 0.3:
            return ContentComplexity.MODERATE
        else:
            return ContentComplexity.SIMPLE

    def _assess_image_quality(self, image: np.ndarray) -> ImageQuality:
        """Assess image quality based on various metrics"""

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Calculate quality metrics
        blur_score = self._calculate_blur_score(gray)
        noise_score = self._calculate_noise_score(gray)
        contrast_score = self._calculate_contrast_score(gray)

        # Combine metrics (lower scores = better quality)
        quality_score = (blur_score + noise_score + (1 - contrast_score)) / 3

        if quality_score < 0.2:
            return ImageQuality.EXCELLENT
        elif quality_score < 0.4:
            return ImageQuality.GOOD
        elif quality_score < 0.6:
            return ImageQuality.FAIR
        elif quality_score < 0.8:
            return ImageQuality.POOR
        else:
            return ImageQuality.VERY_POOR

    def _analyze_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze document layout characteristics"""

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        return {
            "has_tables": self._detect_tables(gray),
            "has_forms": self._detect_forms(gray),
            "has_lines": self._detect_lines(gray),
            "text_density": self._calculate_text_density(gray),
            "layout_complexity": self._calculate_layout_complexity(gray),
            "estimated_columns": self._estimate_columns(gray)
        }

    def _detect_language(self, image: np.ndarray) -> str:
        """Simple language detection based on character analysis"""
        # This is a simplified version - real implementation would use OCR
        # For now, default to English
        return "en"

    def _generate_backend_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate optimal backend recommendations based on analysis"""

        doc_type = analysis["document_type"]
        complexity = analysis["content_complexity"]
        quality = analysis["image_quality"]

        recommendations = []

        # Primary recommendations based on document type
        if doc_type == DocumentType.MATHEMATICAL:
            recommendations.extend(["deepseek-ocr", "florence-2", "mistral-ocr"])
        elif doc_type == DocumentType.TABLE:
            recommendations.extend(["dots-ocr", "florence-2", "mistral-ocr"])
        elif doc_type == DocumentType.FORM:
            recommendations.extend(["mistral-ocr", "florence-2", "dots-ocr"])
        elif doc_type == DocumentType.COMIC:
            recommendations.extend(["qwen-layered", "florence-2", "deepseek-ocr"])
        elif doc_type == DocumentType.HANDWRITING:
            recommendations.extend(["florence-2", "deepseek-ocr", "easyocr"])
        elif doc_type == DocumentType.MIXED_CONTENT:
            recommendations.extend(["mistral-ocr", "deepseek-ocr", "florence-2"])
        elif doc_type == DocumentType.PRINTED_TEXT:
            if complexity == ContentComplexity.SIMPLE:
                recommendations.extend(["pp-ocrv5", "tesseract", "easyocr"])
            else:
                recommendations.extend(["mistral-ocr", "deepseek-ocr", "florence-2"])

        # Adjust for image quality
        if quality in [ImageQuality.POOR, ImageQuality.VERY_POOR]:
            # Prefer robust backends for poor quality images
            if "florence-2" not in recommendations:
                recommendations.insert(0, "florence-2")
            if "deepseek-ocr" not in recommendations:
                recommendations.insert(0, "deepseek-ocr")

        # Fallback to auto-selection
        if not recommendations:
            recommendations = ["auto"]

        return recommendations[:3]  # Return top 3 recommendations

    # Helper methods for analysis
    def _calculate_text_density(self, gray: np.ndarray) -> float:
        """Calculate text density (0-1)"""
        # Simple thresholding and contour analysis
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Calculate area covered by contours
        total_area = gray.shape[0] * gray.shape[1]
        contour_area = sum(cv2.contourArea(contour) for contour in contours)

        return min(contour_area / total_area, 1.0) if total_area > 0 else 0.0

    def _detect_tables(self, gray: np.ndarray) -> bool:
        """Detect table-like structures"""
        # Look for horizontal and vertical lines
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)

        if lines is None:
            return False

        # Count horizontal and vertical lines
        h_lines = sum(1 for line in lines[0] if abs(line[1] - line[3]) < 10)  # horizontal
        v_lines = sum(1 for line in lines[0] if abs(line[0] - line[2]) < 10)  # vertical

        return h_lines > 2 and v_lines > 2

    def _detect_forms(self, gray: np.ndarray) -> bool:
        """Detect form-like elements (checkboxes, text fields)"""
        # Look for rectangular shapes that could be form fields
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        rectangles = []
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)

            if len(approx) == 4:  # Rectangle
                area = cv2.contourArea(contour)
                if 100 < area < 10000:  # Reasonable size for form fields
                    rectangles.append(contour)

        return len(rectangles) > 3  # Multiple rectangles suggest a form

    def _detect_lines(self, gray: np.ndarray) -> bool:
        """Detect straight lines in the document"""
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 200)

        return lines is not None and len(lines) > 5

    def _calculate_color_variance(self, image: np.ndarray) -> float:
        """Calculate color variance to detect colorful content"""
        return np.var(image.astype(np.float32))

    def _detect_mathematical_symbols(self, gray: np.ndarray) -> bool:
        """Detect mathematical symbols and formulas"""
        # This is a simplified detection - real implementation would use OCR
        # Look for patterns that might indicate mathematical content
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Count small contours that might be mathematical symbols
        small_contours = [c for c in contours if 20 < cv2.contourArea(c) < 500]
        return len(small_contours) > 10

    def _detect_receipt_patterns(self, gray: np.ndarray) -> bool:
        """Detect receipt-like patterns"""
        height, width = gray.shape
        aspect_ratio = width / height

        # Receipts are typically tall and narrow
        if aspect_ratio < 0.5 and height > width:
            return True

        return False

    def _detect_handwriting(self, gray: np.ndarray) -> bool:
        """Detect handwriting characteristics"""
        # Handwriting typically has more curved lines and less uniformity
        edges = cv2.Canny(gray, 50, 150)

        # Count edge pixels
        edge_density = np.sum(edges > 0) / edges.size

        # Handwriting tends to have higher edge density due to variable stroke widths
        return edge_density > 0.05

    def _detect_scanned_artifacts(self, gray: np.ndarray) -> bool:
        """Detect scanning artifacts"""
        # Look for patterns typical of scanned documents
        # This could include bleed-through, paper texture, etc.
        # Simplified version: check for noise patterns
        blur_score = self._calculate_blur_score(gray)
        return blur_score > 100  # High blur suggests scanning artifacts

    def _calculate_layout_complexity(self, gray: np.ndarray) -> float:
        """Calculate layout complexity score"""
        # Measure text distribution and layout patterns
        edges = cv2.Canny(gray, 50, 150)

        # Divide image into regions and check text distribution
        h, w = gray.shape
        regions = []
        for i in range(3):
            for j in range(3):
                y1, y2 = i * h // 3, (i + 1) * h // 3
                x1, x2 = j * w // 3, (j + 1) * w // 3
                region = edges[y1:y2, x1:x2]
                text_density = np.sum(region > 0) / region.size
                regions.append(text_density)

        # Calculate variance in text distribution
        return np.std(regions)

    def _estimate_columns(self, gray: np.ndarray) -> int:
        """Estimate number of columns in document"""
        # Simplified column detection
        h, w = gray.shape

        # Check vertical distribution of text
        vertical_projection = np.sum(gray < 128, axis=0)  # Sum along vertical axis

        # Find peaks in vertical projection
        peaks = []
        threshold = np.max(vertical_projection) * 0.3

        for i in range(1, len(vertical_projection) - 1):
            if (vertical_projection[i] > vertical_projection[i-1] and
                vertical_projection[i] > vertical_projection[i+1] and
                vertical_projection[i] > threshold):
                peaks.append(i)

        return max(1, len(peaks) + 1)

    def _calculate_blur_score(self, gray: np.ndarray) -> float:
        """Calculate blur score (lower = sharper)"""
        # Laplacian variance method
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def _calculate_noise_score(self, gray: np.ndarray) -> float:
        """Calculate noise score (lower = less noise)"""
        # Simple noise estimation using local variance
        kernel = np.ones((5, 5), np.float32) / 25
        mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        sqmean = cv2.filter2D(gray.astype(np.float32)**2, -1, kernel)
        variance = sqmean - mean**2

        return np.mean(variance)

    def _calculate_contrast_score(self, gray: np.ndarray) -> float:
        """Calculate contrast score (0-1, higher = better contrast)"""
        return (np.max(gray) - np.min(gray)) / 255.0


class BackendOptimizer:
    """Intelligent backend selection and optimization"""

    def __init__(self, config: OCRConfig):
        self.config = config
        self.analyzer = DocumentAnalyzer(config)

    def select_optimal_backend(self, image_path: Path, requested_backend: str = "auto") -> str:
        """
        Select the optimal backend based on document analysis

        Args:
            image_path: Path to the document image
            requested_backend: User-requested backend ("auto" for intelligent selection)

        Returns:
            Optimal backend name
        """
        if requested_backend != "auto":
            return requested_backend

        try:
            # Analyze the document
            analysis = self.analyzer.analyze_document(image_path)

            # Get backend recommendations
            recommendations = analysis.get("backend_recommendations", ["auto"])

            if recommendations and recommendations[0] != "auto":
                optimal_backend = recommendations[0]
                logger.info(f"Selected optimal backend '{optimal_backend}' for {image_path.name} "
                          f"(type: {analysis['document_type'].value}, "
                          f"complexity: {analysis['content_complexity'].value})")
                return optimal_backend
            else:
                logger.info(f"Using auto-selection for {image_path.name}")
                return "auto"

        except Exception as e:
            logger.warning(f"Backend optimization failed for {image_path}: {e}, using auto-selection")
            return "auto"

    def get_backend_performance_profile(self, backend_name: str) -> Dict[str, Any]:
        """Get performance profile for a backend based on document characteristics"""

        profiles = {
            "mistral-ocr": {
                "strengths": ["enterprise_docs", "forms", "scanned_docs", "tables", "mixed_content"],
                "weaknesses": [],
                "speed": "medium",
                "accuracy": "very_high",
                "gpu_memory": "high",
                "offline": False
            },
            "deepseek-ocr": {
                "strengths": ["complex_layouts", "mathematical", "multilingual", "mixed_content"],
                "weaknesses": [],
                "speed": "medium",
                "accuracy": "very_high",
                "gpu_memory": "high",
                "offline": True
            },
            "florence-2": {
                "strengths": ["layout_analysis", "handwriting", "forms", "tables"],
                "weaknesses": [],
                "speed": "medium",
                "accuracy": "high",
                "gpu_memory": "medium",
                "offline": True
            },
            "dots-ocr": {
                "strengths": ["tables", "structured_docs", "forms"],
                "weaknesses": ["plain_text"],
                "speed": "fast",
                "accuracy": "high",
                "gpu_memory": "medium",
                "offline": True
            },
            "pp-ocrv5": {
                "strengths": ["printed_text", "speed", "industrial"],
                "weaknesses": ["handwriting", "complex_layouts"],
                "speed": "very_fast",
                "accuracy": "high",
                "gpu_memory": "low",
                "offline": True
            },
            "qwen-layered": {
                "strengths": ["comics", "mixed_content", "layered_images"],
                "weaknesses": ["plain_text"],
                "speed": "medium",
                "accuracy": "high",
                "gpu_memory": "high",
                "offline": True
            },
            "tesseract": {
                "strengths": ["printed_text", "multilingual"],
                "weaknesses": ["handwriting", "complex_layouts"],
                "speed": "very_fast",
                "accuracy": "medium",
                "gpu_memory": "none",
                "offline": True
            },
            "easyocr": {
                "strengths": ["handwriting", "multilingual"],
                "weaknesses": ["printed_text"],
                "speed": "slow",
                "accuracy": "medium",
                "gpu_memory": "low",
                "offline": True
            }
        }

        return profiles.get(backend_name, {
            "strengths": [],
            "weaknesses": [],
            "speed": "unknown",
            "accuracy": "unknown",
            "gpu_memory": "unknown",
            "offline": False
        })

    def get_document_analysis(self, image_path: Path) -> Dict[str, Any]:
        """Get full document analysis for external use"""
        return self.analyzer.analyze_document(image_path)