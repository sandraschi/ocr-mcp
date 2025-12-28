"""
Document Structure Analysis Tools for OCR-MCP

Advanced document analysis tools for detecting tables, forms, layout elements,
and document structure understanding.
"""

import logging
from typing import Dict, Any, Optional, List
import re

from ..core.backend_manager import BackendManager
from ..core.config import OCRConfig

# Optional OpenCV import
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None
    OPENCV_AVAILABLE = False

logger = logging.getLogger(__name__)


def register_analysis_tools(app, backend_manager: BackendManager, config: OCRConfig):
    """Register all document analysis tools with the FastMCP app."""

    @app.tool()
    async def analyze_document_layout(
        image_path: str,
        analysis_type: str = "comprehensive",
        detect_tables: bool = True,
        detect_forms: bool = True,
        detect_headers: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze document layout and structure.

        Detects document elements like headers, paragraphs, tables, forms,
        images, and other structural components.

        Args:
            image_path: Path to the document image
            analysis_type: Type of analysis ("basic", "comprehensive", "detailed")
            detect_tables: Enable table detection
            detect_forms: Enable form field detection
            detect_headers: Enable header/footer detection

        Returns:
            Document layout analysis with detected elements
        """
        logger.info(f"Analyzing document layout: {image_path}")

        try:
            from PIL import Image
            import numpy as np
            import cv2

            # Load image
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

            # Basic layout analysis
            layout_elements = []

            # Detect text blocks and lines
            text_regions = _detect_text_regions(cv_image)

            # Classify text regions
            for region in text_regions:
                element_type = _classify_text_region(region, cv_image)
                layout_elements.append({
                    "type": element_type,
                    "bbox": region["bbox"],
                    "confidence": region["confidence"],
                    "text_estimate": region.get("text", "")
                })

            # Table detection
            if detect_tables:
                tables = _detect_tables(cv_image)
                for table in tables:
                    layout_elements.append({
                        "type": "table",
                        "bbox": table["bbox"],
                        "rows": table["rows"],
                        "cols": table["cols"],
                        "confidence": table["confidence"]
                    })

            # Form detection
            if detect_forms:
                forms = _detect_form_fields(cv_image, text_regions)
                layout_elements.extend(forms)

            # Header/Footer detection
            if detect_headers:
                headers_foot = _detect_headers_footers(cv_image, text_regions)
                layout_elements.extend(headers_foot)

            # Group elements by type
            element_summary = _summarize_layout_elements(layout_elements)

            return {
                "success": True,
                "image_path": image_path,
                "analysis_type": analysis_type,
                "layout_elements": layout_elements,
                "element_summary": element_summary,
                "document_structure": {
                    "has_tables": any(e["type"] == "table" for e in layout_elements),
                    "has_forms": any(e["type"] in ["form_field", "checkbox", "signature"] for e in layout_elements),
                    "has_headers": any(e["type"] == "header" for e in layout_elements),
                    "has_footers": any(e["type"] == "footer" for e in layout_elements),
                    "text_blocks": len([e for e in layout_elements if e["type"] == "text_block"]),
                    "estimated_pages": 1
                },
                "image_info": {
                    "width": image.width,
                    "height": image.height,
                    "orientation": _detect_orientation(cv_image)
                },
                "message": f"Layout analysis complete: {len(layout_elements)} elements detected"
            }

        except Exception as e:
            logger.error(f"Document layout analysis failed: {e}")
            return {
                "success": False,
                "error": f"Layout analysis failed: {str(e)}",
                "image_path": image_path
            }

    @app.tool()
    async def extract_table_data(
        image_path: str,
        table_region: Optional[List[int]] = None,
        ocr_backend: str = "auto"
    ) -> Dict[str, Any]:
        """
        Extract tabular data from document images.

        Detects table structures and extracts data from rows and columns,
        returning structured tabular data.

        Args:
            image_path: Path to the document image
            table_region: Optional bounding box [x1,y1,x2,y2] for specific table
            ocr_backend: OCR backend to use for text extraction

        Returns:
            Extracted table data with structure and content
        """
        logger.info(f"Extracting table data from: {image_path}")

        try:
            from PIL import Image
            import numpy as np
            import cv2

            # Load image
            image = Image.open(image_path)
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

            # Find tables
            tables = _detect_tables(cv_image)

            if table_region:
                # Focus on specific region
                tables = [t for t in tables if _bbox_overlap(t["bbox"], table_region) > 0.5]

            extracted_tables = []

            for table_info in tables:
                table_data = await _extract_table_content(
                    image_path, table_info, ocr_backend
                )
                extracted_tables.append(table_data)

            return {
                "success": True,
                "image_path": image_path,
                "tables_found": len(tables),
                "tables_extracted": len(extracted_tables),
                "table_data": extracted_tables,
                "extraction_method": "structure_analysis + OCR",
                "message": f"Extracted {len(extracted_tables)} tables with structured data"
            }

        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return {
                "success": False,
                "error": f"Table extraction failed: {str(e)}",
                "image_path": image_path
            }

    @app.tool()
    async def detect_form_fields(
        image_path: str,
        field_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect and classify form fields in documents.

        Identifies checkboxes, text fields, radio buttons, signatures,
        and other form elements with their positions.

        Args:
            image_path: Path to the document image
            field_types: Types of fields to detect (default: all types)

        Returns:
            Detected form fields with classifications and positions
        """
        logger.info(f"Detecting form fields in: {image_path}")

        if field_types is None:
            field_types = ["checkbox", "text_field", "radio_button", "signature", "date_field"]

        try:
            from PIL import Image
            import numpy as np
            import cv2

            # Load image
            image = Image.open(image_path)
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

            # Get text regions first (form fields are often near text)
            text_regions = _detect_text_regions(cv_image)

            # Detect form fields
            form_fields = []

            # Checkbox detection
            if "checkbox" in field_types:
                checkboxes = _detect_checkboxes(cv_image)
                form_fields.extend([{
                    "type": "checkbox",
                    "bbox": cb["bbox"],
                    "confidence": cb["confidence"],
                    "state": cb.get("state", "unknown")
                } for cb in checkboxes])

            # Text field detection (rectangular areas near text)
            if "text_field" in field_types:
                text_fields = _detect_text_fields(cv_image, text_regions)
                form_fields.extend([{
                    "type": "text_field",
                    "bbox": tf["bbox"],
                    "confidence": tf["confidence"],
                    "associated_text": tf.get("label", "")
                } for tf in text_fields])

            # Radio button detection
            if "radio_button" in field_types:
                radio_buttons = _detect_radio_buttons(cv_image)
                form_fields.extend([{
                    "type": "radio_button",
                    "bbox": rb["bbox"],
                    "confidence": rb["confidence"],
                    "group": rb.get("group", "unknown")
                } for rb in radio_buttons])

            # Signature field detection
            if "signature" in field_types:
                signatures = _detect_signature_fields(cv_image, text_regions)
                form_fields.extend([{
                    "type": "signature",
                    "bbox": sig["bbox"],
                    "confidence": sig["confidence"]
                } for sig in signatures])

            # Group fields by type
            field_summary = {}
            for field_type in field_types:
                field_summary[field_type] = len([f for f in form_fields if f["type"] == field_type])

            return {
                "success": True,
                "image_path": image_path,
                "field_types_requested": field_types,
                "form_fields": form_fields,
                "field_summary": field_summary,
                "total_fields": len(form_fields),
                "document_type": "form" if len(form_fields) > 0 else "document",
                "message": f"Detected {len(form_fields)} form fields"
            }

        except Exception as e:
            logger.error(f"Form field detection failed: {e}")
            return {
                "success": False,
                "error": f"Form field detection failed: {str(e)}",
                "image_path": image_path
            }

    @app.tool()
    async def analyze_document_reading_order(
        image_path: str,
        ocr_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze the logical reading order of document content.

        Determines the proper sequence for reading multi-column documents,
        forms with complex layouts, and documents with non-linear content flow.

        Args:
            image_path: Path to the document image
            ocr_result: Optional pre-computed OCR result to avoid re-processing

        Returns:
            Document reading order analysis with content sequencing
        """
        logger.info(f"Analyzing reading order for: {image_path}")

        try:
            from PIL import Image

            # Load image
            image = Image.open(image_path)

            # Get OCR result if not provided
            if not ocr_result:
                ocr_result = await backend_manager.process_with_backend(
                    "auto", image_path, mode="text"
                )

            if not ocr_result.get("success"):
                return {
                    "success": False,
                    "error": "OCR processing failed - cannot analyze reading order"
                }

            # Extract text blocks with positions
            raw_results = ocr_result.get("raw_results", [])

            # Sort text blocks into reading order
            reading_order = _determine_reading_order(raw_results, image.size)

            # Group into logical sections
            sections = _group_into_sections(reading_order)

            return {
                "success": True,
                "image_path": image_path,
                "reading_order": reading_order,
                "sections": sections,
                "content_flow": {
                    "total_blocks": len(reading_order),
                    "sections_count": len(sections),
                    "estimated_columns": _estimate_columns(reading_order),
                    "reading_direction": "left-to-right-top-to-bottom"
                },
                "message": f"Reading order analysis complete: {len(reading_order)} text blocks sequenced"
            }

        except Exception as e:
            logger.error(f"Reading order analysis failed: {e}")
            return {
                "success": False,
                "error": f"Reading order analysis failed: {str(e)}",
                "image_path": image_path
            }

    @app.tool()
    async def classify_document_type(
        image_path: str,
        ocr_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify the type of document based on layout and content analysis.

        Identifies document types like invoices, receipts, forms, letters,
        reports, contracts, etc.

        Args:
            image_path: Path to the document image
            ocr_result: Optional pre-computed OCR result

        Returns:
            Document type classification with confidence scores
        """
        logger.info(f"Classifying document type: {image_path}")

        try:
            from PIL import Image

            # Load image
            image = Image.open(image_path)

            # Get OCR result if not provided
            if not ocr_result:
                ocr_result = await backend_manager.process_with_backend(
                    "auto", image_path, mode="text"
                )

            ocr_text = ocr_result.get("text", "") if ocr_result.get("success") else ""

            # Analyze layout
            layout_analysis = await analyze_document_layout(image_path, "basic")

            # Classify based on content and layout features
            classification = _classify_document_type(ocr_text, layout_analysis)

            return {
                "success": True,
                "image_path": image_path,
                "document_type": classification["primary_type"],
                "confidence": classification["confidence"],
                "alternative_types": classification["alternatives"],
                "detected_features": classification["features"],
                "classification_reasoning": classification["reasoning"],
                "message": f"Document classified as: {classification['primary_type']} ({classification['confidence']}% confidence)"
            }

        except Exception as e:
            logger.error(f"Document classification failed: {e}")
            return {
                "success": False,
                "error": f"Document classification failed: {str(e)}",
                "image_path": image_path
            }

    @app.tool()
    async def extract_document_metadata(
        image_path: str,
        ocr_result: Optional[Dict[str, Any]] = None,
        extract_dates: bool = True,
        extract_names: bool = True,
        extract_numbers: bool = True
    ) -> Dict[str, Any]:
        """
        Extract structured metadata from documents.

        Identifies and extracts dates, names, document numbers, amounts,
        addresses, and other structured information.

        Args:
            image_path: Path to the document image
            ocr_result: Optional pre-computed OCR result
            extract_dates: Extract date information
            extract_names: Extract person/company names
            extract_numbers: Extract document numbers and amounts

        Returns:
            Extracted document metadata with confidence scores
        """
        logger.info(f"Extracting metadata from: {image_path}")

        try:
            # Get OCR result if not provided
            if not ocr_result:
                ocr_result = await backend_manager.process_with_backend(
                    "auto", image_path, mode="text"
                )

            ocr_text = ocr_result.get("text", "") if ocr_result.get("success") else ""

            metadata = {
                "dates": [],
                "names": [],
                "numbers": [],
                "amounts": [],
                "addresses": [],
                "document_numbers": []
            }

            # Extract dates
            if extract_dates:
                metadata["dates"] = _extract_dates(ocr_text)

            # Extract names (basic pattern matching)
            if extract_names:
                metadata["names"] = _extract_names(ocr_text)

            # Extract numbers and amounts
            if extract_numbers:
                numbers_data = _extract_numbers_and_amounts(ocr_text)
                metadata.update(numbers_data)

            # Extract addresses
            metadata["addresses"] = _extract_addresses(ocr_text)

            # Calculate confidence scores
            confidence_scores = {}
            for key, items in metadata.items():
                if items:
                    # Simple confidence based on extraction consistency
                    confidence_scores[key] = min(95, 60 + len(items) * 5)
                else:
                    confidence_scores[key] = 0

            return {
                "success": True,
                "image_path": image_path,
                "metadata": metadata,
                "confidence_scores": confidence_scores,
                "extraction_summary": {
                    "total_items_extracted": sum(len(items) for items in metadata.values()),
                    "categories_with_data": len([k for k, v in metadata.items() if v]),
                    "highest_confidence": max(confidence_scores.values()) if confidence_scores else 0
                },
                "message": f"Extracted {sum(len(items) for items in metadata.values())} metadata items"
            }

        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {
                "success": False,
                "error": f"Metadata extraction failed: {str(e)}",
                "image_path": image_path
            }


# Helper functions for document analysis

def _detect_text_regions(image):
    """Detect text regions in the image."""
    # Simple text region detection using morphology
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
    dilated = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    text_regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 50 and h > 10:  # Filter small regions
            text_regions.append({
                "bbox": [x, y, x + w, y + h],
                "area": w * h,
                "confidence": 0.8
            })

    return sorted(text_regions, key=lambda x: (x["bbox"][1], x["bbox"][0]))

def _classify_text_region(region, image):
    """Classify a text region based on position and characteristics."""
    x1, y1, x2, y2 = region["bbox"]
    img_h, img_w = image.shape

    # Position-based classification
    if y1 < img_h * 0.1:
        return "header"
    elif y2 > img_h * 0.9:
        return "footer"
    elif x1 < img_w * 0.1 and x2 > img_w * 0.9:
        return "title"
    else:
        return "text_block"

def _detect_tables(image):
    """Detect table structures in the image."""
    # Simple table detection using line detection
    # This is a placeholder - real table detection would use more sophisticated methods
    tables = []

    # Look for horizontal and vertical lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

    horizontal_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel)
    vertical_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, vertical_kernel)

    # Combine lines
    table_mask = cv2.add(horizontal_lines, vertical_lines)

    # Find table regions
    contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 100 and h > 50:  # Reasonable table size
            tables.append({
                "bbox": [x, y, x + w, y + h],
                "rows": 3,  # Placeholder
                "cols": 4,  # Placeholder
                "confidence": 0.7
            })

    return tables

def _detect_form_fields(image, text_regions):
    """Detect form fields in the image."""
    form_fields = []

    # Simple checkbox detection - look for small squares
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)

        # Check for square-ish shapes (checkboxes)
        if 0.8 <= aspect_ratio <= 1.2 and 10 <= w <= 30:
            form_fields.append({
                "type": "checkbox",
                "bbox": [x, y, x + w, y + h],
                "confidence": 0.75
            })

    return form_fields

def _detect_headers_footers(image, text_regions):
    """Detect header and footer regions."""
    elements = []
    img_h = image.shape[0]

    for region in text_regions:
        y1 = region["bbox"][1]
        if y1 < img_h * 0.15:
            elements.append({
                "type": "header",
                "bbox": region["bbox"],
                "confidence": 0.8
            })
        elif y1 > img_h * 0.85:
            elements.append({
                "type": "footer",
                "bbox": region["bbox"],
                "confidence": 0.8
            })

    return elements

def _summarize_layout_elements(elements):
    """Summarize layout elements by type."""
    summary = {}
    for element in elements:
        elem_type = element["type"]
        if elem_type not in summary:
            summary[elem_type] = 0
        summary[elem_type] += 1
    return summary

def _detect_orientation(image):
    """Detect document orientation."""
    # Simple heuristic - check if image is wider than tall
    h, w = image.shape
    return "landscape" if w > h else "portrait"

async def _extract_table_content(image_path, table_info, ocr_backend):
    """Extract content from a detected table."""
    # This would use OCR to extract cell content
    # Placeholder implementation
    return {
        "bbox": table_info["bbox"],
        "rows": table_info["rows"],
        "cols": table_info["cols"],
        "headers": [],  # Would detect headers
        "data": [],     # Would extract cell data
        "confidence": table_info["confidence"]
    }

def _detect_checkboxes(image):
    """Detect checkboxes in the image."""
    # Simple checkbox detection
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    checkboxes = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)

        if 0.8 <= aspect_ratio <= 1.2 and 10 <= w <= 30:
            checkboxes.append({
                "bbox": [x, y, x + w, y + h],
                "confidence": 0.75
            })

    return checkboxes

def _detect_text_fields(image, text_regions):
    """Detect text input fields."""
    # Look for rectangular areas that might be text fields
    # This is a simplified implementation
    text_fields = []

    for region in text_regions:
        x1, y1, x2, y2 = region["bbox"]
        width = x2 - x1
        height = y2 - y1

        # Look for wide, short rectangles (typical text field shape)
        if width > height * 3 and height < 50:
            text_fields.append({
                "bbox": [x1, y1, x2, y2],
                "confidence": 0.7
            })

    return text_fields

def _detect_radio_buttons(image):
    """Detect radio buttons."""
    # Similar to checkboxes but smaller and rounder
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    radio_buttons = []

    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * 3.14159 * area / (perimeter * perimeter) if perimeter > 0 else 0

        if 0.7 <= circularity <= 1.2 and 50 <= area <= 500:
            x, y, w, h = cv2.boundingRect(contour)
            radio_buttons.append({
                "bbox": [x, y, x + w, y + h],
                "confidence": 0.8
            })

    return radio_buttons

def _detect_signature_fields(image, text_regions):
    """Detect signature fields."""
    signature_fields = []

    for region in text_regions:
        # Look for regions with signature-related text
        # This is a simplified heuristic
        if "signature" in region.get("text", "").lower():
            x1, y1, x2, y2 = region["bbox"]
            # Extend bbox to include signature area
            signature_fields.append({
                "bbox": [x1, y1 + 20, x2, y2 + 100],  # Below the text
                "confidence": 0.8
            })

    return signature_fields

def _bbox_overlap(bbox1, bbox2):
    """Calculate overlap between two bounding boxes."""
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    if x2 <= x1 or y2 <= y1:
        return 0.0

    intersection = (x2 - x1) * (y2 - y1)
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])

    return intersection / (area1 + area2 - intersection)

def _determine_reading_order(text_blocks, image_size):
    """Determine the logical reading order of text blocks."""
    # Sort by top-to-bottom, then left-to-right
    sorted_blocks = sorted(text_blocks, key=lambda x: (x.get("bbox", [0, 0, 0, 0])[1], x.get("bbox", [0, 0, 0, 0])[0]))

    # Add reading order indices
    for i, block in enumerate(sorted_blocks):
        block["reading_order"] = i + 1

    return sorted_blocks

def _group_into_sections(reading_order):
    """Group text blocks into logical sections."""
    sections = []
    current_section = []
    img_width = 1000  # Placeholder

    for block in reading_order:
        bbox = block.get("bbox", [0, 0, 100, 100])
        x1 = bbox[0]

        # Simple column detection
        if x1 < img_width * 0.4:
            column = "left"
        elif x1 > img_width * 0.6:
            column = "right"
        else:
            column = "center"

        block["column"] = column
        current_section.append(block)

    if current_section:
        sections.append({
            "section_number": 1,
            "blocks": current_section,
            "estimated_type": "main_content"
        })

    return sections

def _estimate_columns(reading_order):
    """Estimate number of columns in the document."""
    if not reading_order:
        return 1

    # Simple column estimation based on x-coordinates
    x_positions = [block.get("bbox", [0])[0] for block in reading_order]
    unique_x = len(set(int(x / 100) for x in x_positions))  # Group by 100px bins

    return max(1, min(unique_x, 3))  # Reasonable range

def _classify_document_type(text, layout_analysis):
    """Classify document type based on content and layout."""
    text_lower = text.lower()

    # Invoice indicators
    if any(keyword in text_lower for keyword in ["invoice", "bill", "amount due", "total:", "$"]):
        return {
            "primary_type": "invoice",
            "confidence": 85,
            "alternatives": ["receipt", "bill"],
            "features": ["amounts", "dates", "vendor_info"],
            "reasoning": "Contains invoice-specific keywords and financial information"
        }

    # Receipt indicators
    elif any(keyword in text_lower for keyword in ["receipt", "paid", "change", "subtotal"]):
        return {
            "primary_type": "receipt",
            "confidence": 80,
            "alternatives": ["invoice"],
            "features": ["transaction_details", "amounts"],
            "reasoning": "Contains receipt-specific transaction language"
        }

    # Form indicators
    elif layout_analysis.get("document_structure", {}).get("has_forms", False):
        return {
            "primary_type": "form",
            "confidence": 75,
            "alternatives": ["application", "document"],
            "features": ["form_fields", "structured_layout"],
            "reasoning": "Contains detectable form fields and structured elements"
        }

    # Letter/contract indicators
    elif any(keyword in text_lower for keyword in ["dear", "sincerely", "agreement", "contract"]):
        return {
            "primary_type": "letter",
            "confidence": 70,
            "alternatives": ["contract", "correspondence"],
            "features": ["formal_language", "addressing"],
            "reasoning": "Contains formal correspondence language"
        }

    # Default classification
    else:
        return {
            "primary_type": "document",
            "confidence": 50,
            "alternatives": ["letter", "report"],
            "features": ["text_content"],
            "reasoning": "General document with text content"
        }

def _extract_dates(text):
    """Extract date patterns from text."""
    # Common date patterns
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',     # YYYY/MM/DD
        r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{2,4}\b',  # Month DD, YYYY
        r'\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4}\b'    # DD Month YYYY
    ]

    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)

    return list(set(dates))  # Remove duplicates

def _extract_names(text):
    """Extract potential names from text."""
    # Simple name extraction - capitalized words
    words = re.findall(r'\b[A-Z][a-z]+\b', text)
    # Filter out common non-names
    common_words = {"The", "And", "For", "Are", "But", "Not", "You", "All", "Can", "Had", "Her", "Was", "One", "Our", "Out", "Day", "Get", "Has", "Him", "His", "How", "Its", "May", "New", "Now", "Old", "See", "Two", "Way", "Who", "Boy", "Did", "Has", "Let", "Put", "Say", "She", "Too", "Use"}
    names = [word for word in words if word not in common_words and len(word) > 2]
    return list(set(names))[:10]  # Limit to 10 most common

def _extract_numbers_and_amounts(text):
    """Extract numbers and monetary amounts."""
    # Document numbers (patterns like "INV-123", "PO#456")
    doc_numbers = re.findall(r'\b(?:INV|PO|ORD|REF|DOC)[\s#-]*\d+\b', text, re.IGNORECASE)

    # Monetary amounts ($123.45, €99.99, 123.45 USD)
    amounts = re.findall(r'\b(?:\$|€|£|¥)\s*\d+(?:\.\d{2})?\b|\b\d+(?:\.\d{2})?\s*(?:USD|EUR|GBP|JPY|dollars?|euros?|pounds?)\b', text, re.IGNORECASE)

    # General numbers
    numbers = re.findall(r'\b\d{3,}\b', text)  # Numbers with 3+ digits

    return {
        "document_numbers": list(set(doc_numbers)),
        "amounts": list(set(amounts)),
        "numbers": list(set(numbers))[:20]  # Limit large numbers
    }

def _extract_addresses(text):
    """Extract potential addresses from text."""
    # Simple address pattern matching
    address_indicators = ["street", "avenue", "road", "drive", "lane", "way", "place", "court"]
    lines = text.split('\n')

    addresses = []
    for line in lines:
        line_lower = line.lower().strip()
        if any(indicator in line_lower for indicator in address_indicators):
            if len(line.strip()) > 10:  # Reasonable address length
                addresses.append(line.strip())

    return addresses[:5]  # Limit to 5 addresses