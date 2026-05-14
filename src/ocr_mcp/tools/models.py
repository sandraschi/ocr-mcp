# MIT License
#
# Copyright (c) 2025 OCR-MCP Project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
#
#
#
#

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# Common Literals for Enums
OCRBackend = Literal[
    "auto",
    "deepseek-ocr",
    "deepseek-ocr2",
    "paddleocr-vl",
    "olmocr-2",
    "pp-ocrv5",
    "dots-ocr",
    "got-ocr",
    "qwen-layered",
    "tesseract",
    "easyocr",
    "mistral-ocr",
    "nemotron-vl",
    "florence-2",
]

OCRMode = Literal["auto", "fast", "accurate", "legacy"]

OutputFormat = Literal["text", "markdown", "json", "html", "pdf"]

ErrorSeverity = Literal["low", "medium", "high", "critical"]

ErrorCategory = Literal[
    "file_io",
    "network",
    "model",
    "configuration",
    "validation",
    "processing",
    "resource",
    "backend",
    "scanner",
    "system",
]


# Base Response Models
class BaseResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation was successful")
    operation: str = Field(..., description="The operation that was performed")


class ErrorResponse(BaseResponse):
    success: Literal[False] = False
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Machine-readable error code")
    category: ErrorCategory = Field(..., description="Category of the error")
    severity: ErrorSeverity = Field(..., description="Severity of the error")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    recovery_options: list[str] = Field(default_factory=list, description="Suggestions for recovering from the error")
    recovery_flow: Optional[str] = Field(None, description="Recommended next tool to call for recovery")


# Tool-Specific Result Models
class OCRResult(BaseModel):
    text: str = Field(..., description="Extracted text content")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    backend_used: str = Field(..., description="The OCR backend that performed the extraction")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Document metadata (dates, names, etc.)")
    layout: Optional[dict[str, Any]] = Field(None, description="Layout analysis results")
    pages: Optional[int] = Field(None, description="Number of pages processed")


class ScannerResult(BaseModel):
    device_id: str = Field(..., description="ID of the scanner device")
    file_path: Optional[str] = Field(None, description="Path to the saved scan")
    properties: Optional[dict[str, Any]] = Field(None, description="Scanner properties and capabilities")
    scanners: Optional[list[dict[str, Any]]] = Field(None, description="List of discovered scanners")


class ImageProcessResult(BaseModel):
    source_path: str = Field(..., description="Path to the input image")
    target_path: str = Field(..., description="Path to the processed image")
    operations_applied: list[str] = Field(default_factory=list, description="List of preprocessing steps applied")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Image properties (DPI, dimensions, etc.)")


class WorkflowResult(BaseModel):
    workflow_name: str = Field(..., description="Name of the workflow or pipeline")
    total_documents: int = Field(..., description="Total number of documents processed")
    successful: int = Field(..., description="Number of successfully processed documents")
    failed: int = Field(..., description="Number of documents that failed processing")
    results: list[dict[str, Any]] = Field(default_factory=list, description="Individual result per document")
    final_output: Optional[str] = Field(None, description="Aggregated final output if applicable")


# Combined Tool Responses
class ToolResponse(BaseResponse):
    result: Optional[Any] = Field(None, description="The primary result of the operation")
    summary: Optional[str] = Field(None, description="Human-readable summary of what was done")
    next_steps: list[str] = Field(default_factory=list, description="Recommended next actions for the user/LLM")
    suggestions: list[str] = Field(default_factory=list, description="Optimization or alternative suggestions")
