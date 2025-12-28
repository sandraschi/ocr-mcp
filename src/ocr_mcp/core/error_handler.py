"""
OCR-MCP Error Handler: Comprehensive error handling and user feedback system
"""

import logging
import traceback
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Minor issues, operation can continue
    MEDIUM = "medium"     # Significant issues, operation partially successful
    HIGH = "high"         # Critical issues, operation failed
    CRITICAL = "critical" # System-level failures


class ErrorCategory(Enum):
    """Error categories for better classification"""
    FILE_IO = "file_io"
    NETWORK = "network"
    MODEL = "model"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    PROCESSING = "processing"
    RESOURCE = "resource"
    BACKEND = "backend"
    SCANNER = "scanner"
    SYSTEM = "system"


class OCRError(Exception):
    """Base OCR exception with structured error information"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[List[str]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.error_code = error_code
        self.details = details or {}
        self.recovery_suggestions = recovery_suggestions or []
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to structured dictionary"""
        return {
            "success": False,
            "error": str(self),
            "error_code": self.error_code,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "recovery_suggestions": self.recovery_suggestions,
            "traceback": traceback.format_exc() if logger.isEnabledFor(logging.DEBUG) else None
        }


class ErrorHandler:
    """Centralized error handling and recovery system"""

    # Error code definitions
    ERROR_CODES = {
        # File I/O errors
        "FILE_NOT_FOUND": ("Source file not found", ErrorCategory.FILE_IO, ErrorSeverity.HIGH),
        "FILE_PERMISSION_DENIED": ("Permission denied accessing file", ErrorCategory.FILE_IO, ErrorSeverity.HIGH),
        "FILE_CORRUPTED": ("File appears to be corrupted", ErrorCategory.FILE_IO, ErrorSeverity.HIGH),
        "UNSUPPORTED_FORMAT": ("File format not supported", ErrorCategory.FILE_IO, ErrorSeverity.MEDIUM),

        # Network errors
        "NETWORK_TIMEOUT": ("Network request timed out", ErrorCategory.NETWORK, ErrorSeverity.MEDIUM),
        "NETWORK_UNAVAILABLE": ("Network connection unavailable", ErrorCategory.NETWORK, ErrorSeverity.MEDIUM),
        "API_RATE_LIMITED": ("API rate limit exceeded", ErrorCategory.NETWORK, ErrorSeverity.MEDIUM),

        # Model errors
        "MODEL_NOT_FOUND": ("Required model not found", ErrorCategory.MODEL, ErrorSeverity.HIGH),
        "MODEL_LOAD_FAILED": ("Failed to load model", ErrorCategory.MODEL, ErrorSeverity.CRITICAL),
        "MODEL_INFERENCE_FAILED": ("Model inference failed", ErrorCategory.MODEL, ErrorSeverity.HIGH),

        # Configuration errors
        "CONFIG_INVALID": ("Configuration is invalid", ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH),
        "BACKEND_NOT_CONFIGURED": ("OCR backend not properly configured", ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH),

        # Validation errors
        "PARAMETERS_INVALID": ("Input parameters are invalid", ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM),
        "REGION_INVALID": ("Region coordinates are invalid", ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM),

        # Processing errors
        "PROCESSING_FAILED": ("Document processing failed", ErrorCategory.PROCESSING, ErrorSeverity.HIGH),
        "OCR_FAILED": ("OCR processing failed", ErrorCategory.PROCESSING, ErrorSeverity.HIGH),
        "QUALITY_TOO_LOW": ("Image quality too low for OCR", ErrorCategory.PROCESSING, ErrorSeverity.MEDIUM),

        # Resource errors
        "MEMORY_INSUFFICIENT": ("Insufficient memory for operation", ErrorCategory.RESOURCE, ErrorSeverity.CRITICAL),
        "GPU_MEMORY_INSUFFICIENT": ("Insufficient GPU memory", ErrorCategory.RESOURCE, ErrorSeverity.HIGH),
        "DISK_SPACE_INSUFFICIENT": ("Insufficient disk space", ErrorCategory.RESOURCE, ErrorSeverity.HIGH),

        # Backend errors
        "BACKEND_NOT_AVAILABLE": ("OCR backend not available", ErrorCategory.BACKEND, ErrorSeverity.HIGH),
        "BACKEND_INITIALIZATION_FAILED": ("Backend initialization failed", ErrorCategory.BACKEND, ErrorSeverity.CRITICAL),

        # Scanner errors
        "SCANNER_NOT_FOUND": ("Scanner device not found", ErrorCategory.SCANNER, ErrorSeverity.HIGH),
        "SCANNER_BUSY": ("Scanner is busy or in use", ErrorCategory.SCANNER, ErrorSeverity.MEDIUM),
        "SCANNER_HARDWARE_ERROR": ("Scanner hardware error", ErrorCategory.SCANNER, ErrorSeverity.HIGH),

        # System errors
        "DEPENDENCY_MISSING": ("Required dependency not installed", ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL),
        "SYSTEM_INCOMPATIBLE": ("System incompatible with operation", ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL),
    }

    @classmethod
    def create_error(
        cls,
        error_code: str,
        message_override: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> OCRError:
        """Create a structured OCR error"""

        if error_code not in cls.ERROR_CODES:
            # Fallback for unknown error codes
            return OCRError(
                message_override or f"Unknown error: {error_code}",
                ErrorCategory.SYSTEM,
                ErrorSeverity.HIGH,
                error_code,
                details,
                cause=cause
            )

        base_message, category, severity = cls.ERROR_CODES[error_code]
        message = message_override or base_message

        # Generate recovery suggestions based on error type
        recovery_suggestions = cls._generate_recovery_suggestions(error_code, details)

        return OCRError(
            message=message,
            category=category,
            severity=severity,
            error_code=error_code,
            details=details or {},
            recovery_suggestions=recovery_suggestions,
            cause=cause
        )

    @classmethod
    def _generate_recovery_suggestions(cls, error_code: str, details: Optional[Dict[str, Any]]) -> List[str]:
        """Generate contextual recovery suggestions"""

        suggestions = {
            "FILE_NOT_FOUND": [
                "Verify the file path is correct",
                "Check file permissions",
                "Ensure the file hasn't been moved or deleted"
            ],
            "MODEL_NOT_FOUND": [
                "Run the model installation script: python scripts/install_models.py",
                "Check available disk space (models require several GB)",
                "Verify internet connection for model downloads"
            ],
            "BACKEND_NOT_AVAILABLE": [
                "Check backend status: Use the ocr_health_check tool",
                "Install missing dependencies for the backend",
                "Try a different OCR backend"
            ],
            "GPU_MEMORY_INSUFFICIENT": [
                "Reduce batch size or image resolution",
                "Close other GPU-intensive applications",
                "Use CPU backend instead: backend='tesseract'"
            ],
            "SCANNER_NOT_FOUND": [
                "Ensure scanner is powered on and connected",
                "Check scanner device in Device Manager (Windows)",
                "Try using a different scanner device ID"
            ],
            "NETWORK_TIMEOUT": [
                "Check internet connection",
                "Increase timeout value if available",
                "Try again later or use offline backends"
            ],
            "QUALITY_TOO_LOW": [
                "Use image enhancement: enhance_image=True",
                "Increase image resolution if possible",
                "Try a different OCR backend better suited for low-quality images"
            ],
            "MEMORY_INSUFFICIENT": [
                "Close other memory-intensive applications",
                "Process files individually instead of batch processing",
                "Reduce image size or use lower quality settings"
            ]
        }

        return suggestions.get(error_code, ["Contact support for assistance"])

    @classmethod
    def handle_exception(
        cls,
        exc: Exception,
        context: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle arbitrary exceptions and convert to structured error response"""

        logger.error(f"Exception in {context or 'unknown context'}: {exc}", exc_info=True)

        # Map common exception types to error codes
        if isinstance(exc, FileNotFoundError):
            error_code = "FILE_NOT_FOUND"
        elif isinstance(exc, PermissionError):
            error_code = "FILE_PERMISSION_DENIED"
        elif isinstance(exc, MemoryError):
            error_code = "MEMORY_INSUFFICIENT"
        elif isinstance(exc, ConnectionError) or isinstance(exc, TimeoutError):
            error_code = "NETWORK_TIMEOUT"
        elif isinstance(exc, ImportError):
            error_code = "DEPENDENCY_MISSING"
        elif isinstance(exc, ValueError):
            error_code = "PARAMETERS_INVALID"
        else:
            # Generic processing error for unknown exceptions
            error_code = "PROCESSING_FAILED"

        try:
            ocr_error = cls.create_error(
                error_code=error_code,
                message_override=str(exc),
                details=details,
                cause=exc
            )
            return ocr_error.to_dict()
        except Exception as e:
            # Fallback for error creation failures
            logger.error(f"Failed to create structured error: {e}")
            return {
                "success": False,
                "error": str(exc),
                "error_code": "UNKNOWN_ERROR",
                "category": "system",
                "severity": "high",
                "details": details or {},
                "recovery_suggestions": ["Check logs for more details", "Contact support"]
            }

    @classmethod
    def validate_file_path(cls, file_path: Union[str, Path]) -> Optional[OCRError]:
        """Validate file path and return error if invalid"""

        path = Path(file_path)

        if not path.exists():
            return cls.create_error(
                "FILE_NOT_FOUND",
                details={"file_path": str(file_path)}
            )

        if not path.is_file():
            return cls.create_error(
                "FILE_NOT_FOUND",
                message_override="Path exists but is not a file",
                details={"file_path": str(file_path)}
            )

        try:
            # Test file accessibility
            with open(path, 'rb') as f:
                f.read(1)
        except PermissionError:
            return cls.create_error(
                "FILE_PERMISSION_DENIED",
                details={"file_path": str(file_path)}
            )
        except Exception as e:
            return cls.create_error(
                "FILE_CORRUPTED",
                message_override=f"File access failed: {e}",
                details={"file_path": str(file_path)}
            )

        return None

    @classmethod
    def validate_parameters(cls, **kwargs) -> List[OCRError]:
        """Validate tool parameters and return list of errors"""

        errors = []

        # Validate backend parameter
        if "backend" in kwargs:
            valid_backends = [
                "auto", "deepseek-ocr", "florence-2", "dots-ocr", "pp-ocrv5",
                "qwen-layered", "got-ocr", "tesseract", "easyocr", "mistral"
            ]
            if kwargs["backend"] not in valid_backends:
                errors.append(cls.create_error(
                    "PARAMETERS_INVALID",
                    message_override=f"Invalid backend: {kwargs['backend']}. Valid options: {', '.join(valid_backends)}",
                    details={"parameter": "backend", "value": kwargs["backend"], "valid_options": valid_backends}
                ))

        # Validate region parameter
        if "region" in kwargs and kwargs["region"] is not None:
            region = kwargs["region"]
            if not isinstance(region, list) or len(region) != 4:
                errors.append(cls.create_error(
                    "REGION_INVALID",
                    message_override="Region must be a list of 4 coordinates [x1, y1, x2, y2]",
                    details={"region": region}
                ))
            elif not all(isinstance(coord, (int, float)) for coord in region):
                errors.append(cls.create_error(
                    "REGION_INVALID",
                    message_override="Region coordinates must be numbers",
                    details={"region": region}
                ))

        return errors


def with_error_handling(func):
    """Decorator to add comprehensive error handling to tool functions"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OCRError as e:
            logger.error(f"OCR Error in {func.__name__}: {e}")
            return e.to_dict()
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return ErrorHandler.handle_exception(e, context=func.__name__, details=kwargs)

    return wrapper


def create_success_response(data: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a standardized success response"""
    response = {
        "success": True,
        "data": data
    }

    if metadata:
        response["metadata"] = metadata

    return response