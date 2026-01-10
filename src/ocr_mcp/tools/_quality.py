"""
Quality Assessment Tools for OCR-MCP

Provides comprehensive OCR quality assessment, confidence scoring,
accuracy validation, and performance analytics.
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


async def assess_ocr_quality(
    ocr_result: Dict[str, Any],
    ground_truth: Optional[str] = None,
    assessment_type: str = "comprehensive",
    backend_manager: Optional[BackendManager] = None,
    config: Optional[OCRConfig] = None,
) -> Dict[str, Any]:
    """
    Assess the quality and accuracy of OCR results.

    Provides detailed quality metrics, confidence analysis, and
    recommendations for improving OCR accuracy.

    Args:
        ocr_result: OCR result dictionary from any OCR operation
        ground_truth: Optional ground truth text for accuracy calculation
        assessment_type: Type of assessment ("basic", "comprehensive", "detailed")
        backend_manager: Optional backend manager for dependency injection
        config: Optional OCR configuration for dependency injection

    Returns:
        Comprehensive quality assessment with metrics and recommendations
    """
    logger.info(f"Assessing OCR quality (type: {assessment_type})")

    try:
        # Extract OCR text and metadata
        ocr_text = ocr_result.get("text", "").strip()
        confidence_scores = ocr_result.get("confidence", [])
        backend_used = ocr_result.get("backend", "unknown")
        processing_time = ocr_result.get("processing_time", 0)

        # Basic metrics
        metrics = {
            "text_length": len(ocr_text),
            "word_count": len(ocr_text.split()) if ocr_text else 0,
            "line_count": len(ocr_text.split("\n")) if ocr_text else 0,
            "has_special_chars": bool(re.search(r"[^\w\s]", ocr_text)),
            "has_numbers": bool(re.search(r"\d", ocr_text)),
            "processing_time": processing_time,
        }

        # Confidence analysis
        confidence_analysis = {}
        if isinstance(confidence_scores, list) and confidence_scores:
            confidence_analysis = {
                "average_confidence": round(
                    sum(confidence_scores) / len(confidence_scores), 3
                ),
                "min_confidence": round(min(confidence_scores), 3),
                "max_confidence": round(max(confidence_scores), 3),
                "confidence_std": round(
                    (
                        sum(
                            (x - sum(confidence_scores) / len(confidence_scores)) ** 2
                            for x in confidence_scores
                        )
                        / len(confidence_scores)
                    )
                    ** 0.5,
                    3,
                ),
                "low_confidence_count": sum(1 for c in confidence_scores if c < 0.7),
                "high_confidence_count": sum(1 for c in confidence_scores if c >= 0.9),
            }
        elif isinstance(confidence_scores, (int, float)):
            confidence_analysis = {
                "overall_confidence": round(confidence_scores, 3),
                "confidence_level": (
                    "high"
                    if confidence_scores >= 0.9
                    else "medium"
                    if confidence_scores >= 0.7
                    else "low"
                ),
            }

        # Text quality indicators
        quality_indicators = {
            "has_gibberish": _detect_gibberish(ocr_text),
            "has_repeated_chars": bool(
                re.search(r"(.)\1{4,}", ocr_text)
            ),  # 5+ repeated chars
            "has_missing_spaces": bool(
                re.search(r"[a-z][A-Z]", ocr_text)
            ),  # Missing spaces between words
            "has_symbol_clusters": bool(
                re.search(r"[^\w\s]{3,}", ocr_text)
            ),  # 3+ consecutive symbols
            "avg_word_length": (
                round(
                    sum(len(word) for word in ocr_text.split()) / len(ocr_text.split()),
                    1,
                )
                if ocr_text.split()
                else 0
            ),
        }

        # Accuracy assessment if ground truth provided
        accuracy_metrics = {}
        if ground_truth:
            accuracy_metrics = _calculate_accuracy_metrics(ocr_text, ground_truth)

        # Quality score (0-100)
        quality_score = _calculate_quality_score(
            confidence_analysis,
            quality_indicators,
            accuracy_metrics if accuracy_metrics else None,
        )

        # Recommendations
        recommendations = _generate_recommendations(
            quality_score,
            confidence_analysis,
            quality_indicators,
            backend_used,
        )

        # Quality grade
        if quality_score >= 90:
            quality_grade = "A"
            grade_description = "Excellent - High confidence, minimal errors"
        elif quality_score >= 80:
            quality_grade = "B"
            grade_description = "Good - Reliable results with minor issues"
        elif quality_score >= 70:
            quality_grade = "C"
            grade_description = "Fair - Acceptable but may need verification"
        elif quality_score >= 60:
            quality_grade = "D"
            grade_description = "Poor - Significant errors, not recommended"
        else:
            quality_grade = "F"
            grade_description = "Unacceptable - Requires manual reprocessing"

        return {
            "success": True,
            "assessment_type": assessment_type,
            "quality_score": quality_score,
            "quality_grade": quality_grade,
            "grade_description": grade_description,
            "basic_metrics": metrics,
            "confidence_analysis": confidence_analysis,
            "quality_indicators": quality_indicators,
            "accuracy_metrics": accuracy_metrics,
            "recommendations": recommendations,
            "backend_used": backend_used,
            "assessment_complete": True,
        }

    except Exception as e:
        logger.error(f"OCR quality assessment failed: {e}")
        return {
            "success": False,
            "error": f"Quality assessment failed: {str(e)}",
            "assessment_type": assessment_type,
        }


async def compare_ocr_backends(
    image_path: str,
    backends: Optional[List[str]] = None,
    ground_truth: Optional[str] = None,
    backend_manager: Optional[BackendManager] = None,
    config: Optional[OCRConfig] = None,
) -> Dict[str, Any]:
    """
    Compare OCR accuracy across different backends on the same image.

    Useful for selecting the best OCR engine for specific document types
    and understanding performance differences.

    Args:
        image_path: Path to the image file to test
        backends: List of backend names to compare (default: all available)
        ground_truth: Optional ground truth text for accuracy comparison
        backend_manager: Optional backend manager for dependency injection
        config: Optional OCR configuration for dependency injection

    Returns:
        Comparative analysis of OCR backend performance
    """
    logger.info(f"Comparing OCR backends on: {image_path}")

    try:
        if backend_manager is None:
            return {
                "success": False,
                "error": "Backend manager required for comparison",
            }

        # Get available backends if not specified
        if backends is None:
            backends = backend_manager.get_available_backends()

        if not backends:
            return {
                "success": False,
                "error": "No OCR backends available for comparison",
            }

        comparison_results = []
        best_result = None
        best_score = 0

        # Test each backend
        for backend_name in backends:
            try:
                logger.info(f"Testing backend: {backend_name}")

                # Process with this backend
                result = await backend_manager.process_with_backend(
                    backend_name, image_path, mode="text"
                )

                if result.get("success"):
                    # Assess quality
                    quality_assessment = await assess_ocr_quality(
                        result,
                        ground_truth,
                        "comprehensive",
                        backend_manager=backend_manager,
                        config=config,
                    )

                    backend_result = {
                        "backend": backend_name,
                        "success": True,
                        "ocr_text": result.get("text", ""),
                        "confidence": result.get("confidence", 0),
                        "processing_time": result.get("processing_time", 0),
                        "quality_score": quality_assessment.get("quality_score", 0),
                        "quality_grade": quality_assessment.get("quality_grade", "F"),
                        "text_length": len(result.get("text", "")),
                        "error": None,
                    }

                    comparison_results.append(backend_result)

                    # Track best result
                    if quality_assessment.get("quality_score", 0) > best_score:
                        best_score = quality_assessment.get("quality_score", 0)
                        best_result = backend_result

                else:
                    comparison_results.append(
                        {
                            "backend": backend_name,
                            "success": False,
                            "error": result.get("error", "Unknown error"),
                            "quality_score": 0,
                            "quality_grade": "F",
                        }
                    )

            except Exception as e:
                logger.warning(f"Backend {backend_name} failed: {e}")
                comparison_results.append(
                    {
                        "backend": backend_name,
                        "success": False,
                        "error": str(e),
                        "quality_score": 0,
                        "quality_grade": "F",
                    }
                )

        # Sort by quality score
        successful_results = [r for r in comparison_results if r["success"]]
        successful_results.sort(key=lambda x: x["quality_score"], reverse=True)

        # Calculate summary statistics
        if successful_results:
            avg_quality = sum(r["quality_score"] for r in successful_results) / len(
                successful_results
            )
            avg_time = sum(r["processing_time"] for r in successful_results) / len(
                successful_results
            )
        else:
            avg_quality = 0
            avg_time = 0

        return {
            "success": True,
            "image_path": image_path,
            "backends_tested": len(comparison_results),
            "backends_successful": len(successful_results),
            "comparison_results": comparison_results,
            "ranked_results": successful_results,
            "best_backend": best_result["backend"] if best_result else None,
            "best_quality_score": best_score,
            "summary_stats": {
                "average_quality_score": round(avg_quality, 1),
                "average_processing_time": round(avg_time, 2),
                "success_rate": round(
                    len(successful_results) / len(comparison_results) * 100, 1
                ),
            },
            "ground_truth_provided": ground_truth is not None,
            "recommendation": _generate_backend_recommendation(
                successful_results, image_path
            ),
        }

    except Exception as e:
        logger.error(f"OCR backend comparison failed: {e}")
        return {
            "success": False,
            "error": f"Backend comparison failed: {str(e)}",
            "image_path": image_path,
        }


async def validate_ocr_accuracy(
    ocr_text: str, expected_text: str, validation_type: str = "character"
) -> Dict[str, Any]:
    """
    Validate OCR accuracy by comparing against expected text.

    Provides detailed accuracy metrics including character-level,
    word-level, and semantic similarity analysis.

    Args:
        ocr_text: Text produced by OCR
        expected_text: Ground truth text to compare against
        validation_type: Type of validation ("character", "word", "semantic")

    Returns:
        Detailed accuracy validation results
    """
    logger.info(f"Validating OCR accuracy ({validation_type})")

    try:
        # Normalize texts for comparison
        ocr_clean = _normalize_text(ocr_text)
        expected_clean = _normalize_text(expected_text)

        accuracy_metrics = _calculate_accuracy_metrics(ocr_clean, expected_clean)

        # Additional semantic analysis
        semantic_analysis = {}
        if validation_type in ["semantic", "comprehensive"]:
            semantic_analysis = _analyze_semantic_similarity(ocr_clean, expected_clean)

        # Error analysis
        error_analysis = _analyze_ocr_errors(ocr_clean, expected_clean)

        # Overall assessment
        overall_accuracy = accuracy_metrics.get("character_accuracy", 0)

        if overall_accuracy >= 95:
            accuracy_grade = "A+"
            assessment = "Excellent - Near perfect accuracy"
        elif overall_accuracy >= 90:
            accuracy_grade = "A"
            assessment = "Very good - Minor character errors only"
        elif overall_accuracy >= 80:
            accuracy_grade = "B"
            assessment = "Good - Some errors but generally readable"
        elif overall_accuracy >= 70:
            accuracy_grade = "C"
            assessment = "Fair - Significant errors, may need correction"
        elif overall_accuracy >= 60:
            accuracy_grade = "D"
            assessment = "Poor - Many errors, difficult to read"
        else:
            accuracy_grade = "F"
            assessment = "Unacceptable - Requires complete reprocessing"

        return {
            "success": True,
            "validation_type": validation_type,
            "accuracy_metrics": accuracy_metrics,
            "semantic_analysis": semantic_analysis,
            "error_analysis": error_analysis,
            "overall_accuracy": round(overall_accuracy, 2),
            "accuracy_grade": accuracy_grade,
            "assessment": assessment,
            "texts_compared": {
                "ocr_length": len(ocr_clean),
                "expected_length": len(expected_clean),
                "length_difference": abs(len(ocr_clean) - len(expected_clean)),
            },
        }

    except Exception as e:
        logger.error(f"OCR accuracy validation failed: {e}")
        return {
            "success": False,
            "error": f"Accuracy validation failed: {str(e)}",
            "validation_type": validation_type,
        }


async def analyze_image_quality(
    image_path: str, quality_checks: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze image quality factors that affect OCR accuracy.

    Checks for common image quality issues that can reduce OCR performance:
    resolution, contrast, noise, skew, blur, etc.

    Args:
        image_path: Path to the image file to analyze
        quality_checks: List of quality checks to perform (default: all)

    Returns:
        Comprehensive image quality analysis
    """
    logger.info(f"Analyzing image quality: {image_path}")

    if quality_checks is None:
        quality_checks = [
            "resolution",
            "contrast",
            "noise",
            "blur",
            "skew",
            "brightness",
        ]

    try:
        from PIL import Image
        import numpy as np

        if not OPENCV_AVAILABLE:
            return {
                "success": False,
                "error": "OpenCV not available for image quality analysis",
            }

        # Load image
        pil_image = Image.open(image_path)
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        gray_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        quality_analysis = {}
        recommendations = []

        # Resolution check
        if "resolution" in quality_checks:
            dpi = _estimate_dpi(pil_image)
            quality_analysis["resolution"] = {
                "pixels_width": pil_image.width,
                "pixels_height": pil_image.height,
                "estimated_dpi": dpi,
                "sufficient_for_ocr": dpi >= 150,
                "recommended_dpi": 300,
            }
            if dpi < 150:
                recommendations.append(
                    "Increase resolution to at least 150 DPI for better OCR"
                )

        # Contrast analysis
        if "contrast" in quality_checks:
            contrast = _calculate_contrast(gray_image)
            quality_analysis["contrast"] = {
                "contrast_ratio": round(contrast, 2),
                "sufficient_contrast": contrast > 50,
                "contrast_level": (
                    "high" if contrast > 100 else "medium" if contrast > 50 else "low"
                ),
            }
            if contrast <= 50:
                recommendations.append(
                    "Improve image contrast - text should be much darker than background"
                )

        # Noise analysis
        if "noise" in quality_checks:
            noise_level = _estimate_noise(gray_image)
            quality_analysis["noise"] = {
                "noise_level": round(noise_level, 2),
                "low_noise": noise_level < 10,
                "acceptable_noise": noise_level < 20,
            }
            if noise_level >= 20:
                recommendations.append(
                    "Reduce image noise using despeckling or smoothing filters"
                )

        # Blur detection
        if "blur" in quality_checks:
            blur_score = _estimate_blur(gray_image)
            quality_analysis["blur"] = {
                "blur_score": round(blur_score, 2),
                "sharp_image": blur_score > 50,
                "blur_level": (
                    "sharp"
                    if blur_score > 100
                    else "moderate"
                    if blur_score > 50
                    else "blurry"
                ),
            }
            if blur_score <= 50:
                recommendations.append(
                    "Image appears blurry - use sharpening or rescan at higher quality"
                )

        # Brightness analysis
        if "brightness" in quality_checks:
            brightness = _calculate_brightness(gray_image)
            quality_analysis["brightness"] = {
                "brightness_level": round(brightness, 1),
                "optimal_brightness": 80 <= brightness <= 180,
                "brightness_category": (
                    "dark"
                    if brightness < 80
                    else "bright"
                    if brightness > 180
                    else "optimal"
                ),
            }
            if brightness < 80:
                recommendations.append(
                    "Image is too dark - increase brightness or exposure"
                )
            elif brightness > 180:
                recommendations.append(
                    "Image is too bright - reduce brightness or exposure"
                )

        # Skew estimation
        if "skew" in quality_checks:
            skew_angle = _estimate_skew(gray_image)
            quality_analysis["skew"] = {
                "skew_angle_degrees": round(skew_angle, 2),
                "significant_skew": abs(skew_angle) > 1.0,
                "needs_correction": abs(skew_angle) > 2.0,
            }
            if abs(skew_angle) > 2.0:
                recommendations.append(
                    f"Image is skewed by {skew_angle:.1f}° - deskewing recommended"
                )

        # Overall quality score
        quality_score = _calculate_overall_quality_score(quality_analysis)
        quality_grade = (
            "A"
            if quality_score >= 90
            else "B"
            if quality_score >= 80
            else "C"
            if quality_score >= 70
            else "D"
            if quality_score >= 60
            else "F"
        )

        return {
            "success": True,
            "image_path": image_path,
            "quality_checks_performed": quality_checks,
            "quality_analysis": quality_analysis,
            "overall_quality_score": quality_score,
            "quality_grade": quality_grade,
            "recommendations": recommendations,
            "ocr_readiness": "ready" if quality_score >= 70 else "needs_improvement",
            "estimated_ocr_accuracy": _estimate_ocr_accuracy_from_quality(
                quality_score
            ),
        }

    except Exception as e:
        logger.error(f"Image quality analysis failed: {e}")
        return {
            "success": False,
            "error": f"Image quality analysis failed: {str(e)}",
            "image_path": image_path,
        }


# Helper functions


def _detect_gibberish(text: str) -> bool:
    """Simple gibberish detection based on character patterns."""
    if not text:
        return False

    # Check for excessive consonant clusters (likely OCR errors)
    consonant_clusters = len(re.findall(r"[bcdfghjklmnpqrstvwxyz]{4,}", text.lower()))
    total_words = len(text.split())

    if total_words > 0:
        return (consonant_clusters / total_words) > 0.3
    return False


def _calculate_accuracy_metrics(ocr_text: str, ground_truth: str) -> Dict[str, float]:
    """Calculate detailed accuracy metrics."""
    # Character-level accuracy
    ocr_chars = list(ocr_text.replace(" ", ""))
    gt_chars = list(ground_truth.replace(" ", ""))

    correct_chars = sum(1 for o, g in zip(ocr_chars, gt_chars) if o == g)
    char_accuracy = (correct_chars / max(len(gt_chars), 1)) * 100

    # Word-level accuracy
    ocr_words = ocr_text.split()
    gt_words = ground_truth.split()

    correct_words = sum(1 for o, g in zip(ocr_words, gt_words) if o == g)
    word_accuracy = (correct_words / max(len(gt_words), 1)) * 100

    # Sequence matching (longest common subsequence)
    lcs_length = _longest_common_subsequence(ocr_text, ground_truth)
    sequence_accuracy = (lcs_length / max(len(ground_truth), 1)) * 100

    return {
        "character_accuracy": round(char_accuracy, 2),
        "word_accuracy": round(word_accuracy, 2),
        "sequence_accuracy": round(sequence_accuracy, 2),
        "characters_correct": correct_chars,
        "characters_total": len(gt_chars),
        "words_correct": correct_words,
        "words_total": len(gt_words),
    }


def _longest_common_subsequence(text1: str, text2: str) -> int:
    """Calculate length of longest common subsequence."""
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]


def _analyze_semantic_similarity(text1: str, text2: str) -> Dict[str, Any]:
    """Analyze semantic similarity (placeholder for advanced analysis)."""
    # Simple word overlap for now
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    jaccard_similarity = len(intersection) / len(union) if union else 0

    return {
        "word_overlap_similarity": round(jaccard_similarity * 100, 2),
        "unique_words_ocr": len(words1 - words2),
        "unique_words_ground_truth": len(words2 - words1),
        "common_words": len(intersection),
    }


def _analyze_ocr_errors(ocr_text: str, ground_truth: str) -> Dict[str, Any]:
    """Analyze common OCR error patterns."""
    errors = {
        "character_substitutions": [],
        "missing_characters": 0,
        "extra_characters": 0,
        "common_mistakes": {},
    }

    # Simple character-by-character comparison
    ocr_chars = list(ocr_text)
    gt_chars = list(ground_truth)

    min_len = min(len(ocr_chars), len(gt_chars))

    for i in range(min_len):
        if ocr_chars[i] != gt_chars[i]:
            errors["character_substitutions"].append(
                {"position": i, "ocr_char": ocr_chars[i], "correct_char": gt_chars[i]}
            )

    errors["missing_characters"] = max(0, len(gt_chars) - len(ocr_chars))
    errors["extra_characters"] = max(0, len(ocr_chars) - len(gt_chars))

    return errors


def _calculate_quality_score(
    confidence_analysis: Dict,
    quality_indicators: Dict,
    accuracy_metrics: Optional[Dict] = None,
) -> int:
    """Calculate overall quality score (0-100)."""
    score = 50  # Base score

    # Confidence factors (40% weight)
    if confidence_analysis:
        avg_conf = confidence_analysis.get("average_confidence", 0.5)
        score += (avg_conf - 0.5) * 80  # Convert 0.5-1.0 to 0-40 points

    # Quality indicators (30% weight)
    if not quality_indicators.get("has_gibberish", False):
        score += 15
    if not quality_indicators.get("has_repeated_chars", False):
        score += 5
    if not quality_indicators.get("has_missing_spaces", False):
        score += 5
    if not quality_indicators.get("has_symbol_clusters", False):
        score += 5

    # Accuracy metrics (30% weight)
    if accuracy_metrics:
        char_acc = accuracy_metrics.get("character_accuracy", 50)
        score += (char_acc - 50) * 0.6  # 30% of total score

    return max(0, min(100, int(score)))


def _generate_recommendations(
    quality_score: int,
    confidence_analysis: Dict,
    quality_indicators: Dict,
    backend: str,
) -> List[str]:
    """Generate improvement recommendations."""
    recommendations = []

    if quality_score < 70:
        recommendations.append(
            "Consider preprocessing the image (deskew, enhance, crop) before OCR"
        )

    if confidence_analysis and confidence_analysis.get("average_confidence", 1.0) < 0.8:
        recommendations.append(
            "Low confidence detected - try a different OCR backend or improve image quality"
        )

    if quality_indicators.get("has_gibberish", False):
        recommendations.append(
            "OCR produced gibberish - image may be too poor quality or incompatible format"
        )

    if quality_indicators.get("has_missing_spaces", False):
        recommendations.append(
            "Missing word spacing detected - try layout-aware OCR backends"
        )

    # Backend-specific recommendations
    if backend == "tesseract" and quality_score < 80:
        recommendations.append(
            "Tesseract works better with high-contrast, clean images - try preprocessing"
        )

    if backend == "easyocr" and quality_score < 80:
        recommendations.append(
            "EasyOCR is good for handwriting - ensure adequate resolution (200+ DPI)"
        )

    return recommendations


def _generate_backend_recommendation(results: List[Dict], image_path: str) -> str:
    """Generate backend recommendation based on comparison results."""
    if not results:
        return "No backends produced successful results"

    best = results[0]
    backend = best["backend"]

    if backend == "deepseek-ocr":
        return (
            "DeepSeek-OCR performed best - excellent for complex documents and formulas"
        )
    elif backend == "florence-2":
        return "Florence-2 performed best - great for layout understanding and structured content"
    elif backend == "pp-ocrv5":
        return "PP-OCRv5 performed best - reliable industrial-grade OCR"
    elif backend == "easyocr":
        return "EasyOCR performed best - good for general text and handwriting"
    elif backend == "tesseract":
        return "Tesseract performed best - classic OCR, works well with clean text"
    else:
        return f"{backend} performed best for this image type"


def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Remove extra whitespace, convert to lowercase
    return " ".join(text.lower().split())


def _estimate_dpi(image) -> int:
    """Estimate DPI from image dimensions (rough approximation)."""
    # Assume standard document sizes
    width, height = image.size
    # Rough DPI estimation based on common A4 at 300 DPI
    if width > 2000:  # Likely 300+ DPI
        return 300
    elif width > 1500:  # Likely 200-300 DPI
        return 250
    elif width > 1000:  # Likely 150-200 DPI
        return 175
    else:  # Likely low DPI
        return 100


def _calculate_contrast(image_array) -> float:
    """Calculate image contrast using RMS contrast."""
    return image_array.std()


def _estimate_noise(image_array) -> float:
    """Estimate image noise using Laplacian variance."""
    return image_array.var()


def _estimate_blur(image_array) -> float:
    """Estimate image blur using Laplacian variance."""
    laplacian = cv2.Laplacian(image_array, cv2.CV_64F)
    return laplacian.var()


def _calculate_brightness(image_array) -> float:
    """Calculate average image brightness."""
    return image_array.mean()


def _estimate_skew(image_array) -> float:
    """Estimate image skew angle (simplified version)."""
    # This is a placeholder - actual skew detection is complex
    return 0.0


def _calculate_overall_quality_score(analysis: Dict) -> int:
    """Calculate overall image quality score."""
    score = 100

    # Resolution penalty
    if not analysis.get("resolution", {}).get("sufficient_for_ocr", True):
        score -= 30

    # Contrast penalty
    if not analysis.get("contrast", {}).get("sufficient_contrast", True):
        score -= 25

    # Noise penalty
    if not analysis.get("noise", {}).get("acceptable_noise", True):
        score -= 20

    # Blur penalty
    if not analysis.get("blur", {}).get("sharp_image", True):
        score -= 25

    # Brightness penalty
    if not analysis.get("brightness", {}).get("optimal_brightness", True):
        score -= 15

    # Skew penalty
    if analysis.get("skew", {}).get("significant_skew", False):
        score -= 10

    return max(0, score)


def _estimate_ocr_accuracy_from_quality(quality_score: int) -> str:
    """Estimate expected OCR accuracy based on image quality."""
    if quality_score >= 90:
        return "95-100%"
    elif quality_score >= 80:
        return "85-95%"
    elif quality_score >= 70:
        return "75-85%"
    elif quality_score >= 60:
        return "60-75%"
    else:
        return "<60%"
