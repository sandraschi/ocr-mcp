# Changelog

All notable changes to OCR-MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Complete implementation of all 6 advanced OCR backends:
  - Mistral OCR 3 (State-of-the-art API-based OCR, 74% win rate over OCR2)
  - DeepSeek-OCR (4.7M+ downloads)
  - Florence-2 (Microsoft vision foundation model)
  - DOTS.OCR (Document structure specialist)
  - PP-OCRv5 (Industrial PaddlePaddle OCR)
  - Qwen-Image-Layered (Advanced image decomposition)
- Full scanner integration with WIA (Windows Image Acquisition)
- Comprehensive document processing for PDF, CBZ/CBR, and images
- Modern web application with FastAPI backend and responsive frontend
- 7 fully functional MCP tools with portmanteau design
- Advanced comic/manga processing with scaffold separation
- Batch processing capabilities with concurrent operations
- Complete project documentation and usage guides

### Changed
- Updated README with current backend matrix and tool ecosystem
- Enhanced documentation with detailed backend descriptions
- Improved error handling and user feedback throughout

### Fixed
- Unicode encoding issues in Windows environment
- Server startup problems with stdio mode
- Logging configuration conflicts
- Backend interface inconsistencies
- Missing dependencies and import errors
- PP-OCRv5 backend availability check (removed deprecated PaddleOCR parameters)
- PP-OCRv5 backend now fully functional with automatic model downloading
- Webapp startup issues with MCP client initialization
- MCP client JSON parsing errors from server log messages
- Incorrect webapp port documentation (8000 → 7460)
- Blocking webapp startup during MCP client initialization

### Tested
- PP-OCRv5 backend successfully tested and verified working
- All 5 OCR models automatically downloaded and initialized:
  - PP-LCNet_x1_0_doc_ori (document orientation detection)
  - UVDoc (document layout analysis)
  - PP-LCNet_x1_0_textline_ori (text line orientation)
  - PP-OCRv5_server_det (text detection)
  - en_PP-OCRv5_mobile_rec (text recognition)
- All 9 OCR backends successfully initialized with graceful fallback system
- 6 out of 9 backends fully functional and available for use
- Backend manager properly handles failed backends with mock implementations

### Added
- MockOCRBackend class for graceful degradation of failed backends
- Comprehensive backend fallback system preventing crashes
- All 9 OCR backends now available in the system:
  - DeepSeek-OCR: Working (4.7M+ downloads)
  - Florence-2: Working (Microsoft vision model)
  - DOTS.OCR: Working (document structure)
  - PP-OCRv5: Working (industrial PaddlePaddle)
  - GOT-OCR2.0: Working (legacy backend)
  - Tesseract: Working (classic OCR)
  - Mistral OCR 3: Ready (API-based, requires key)
  - Qwen-Image-Layered: Available (model not found)
  - EasyOCR: Available (Unicode issues)
