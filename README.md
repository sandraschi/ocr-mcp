# OCR-MCP

**Two ways to use it:** a **web app** for humans (drag‑and‑drop OCR, scanner, batch) and a **FastMCP 3.1 MCP server** for agentic IDE clients—Claude, Cursor, Windsurf—so agents can run OCR, preprocessing, and workflows as tools. Both use the same 10+ OCR engines, WIA scanner (Windows), and pipelines; one repo.

**GitHub topics** (repo → About → Topics): `ocr`, `mcp`, `fastmcp`, `document-processing`, `scanner`, `wia`, `pdf`, `computer-vision`, `model-context-protocol`, `llm`

[![Version](https://img.shields.io/badge/Version-0.2.0--alpha-blue)](https://github.com/sandraschi/ocr-mcp/releases)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.1-0066CC)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![OCR Engines](https://img.shields.io/badge/OCR%20Engines-10%2B-orange)](README#-ai-models--ocr-engines)
[![Scanner](https://img.shields.io/badge/Scanner-WIA%20%28Windows%29-0078D4?logo=windows)](README#-scanner-integration)
[![Web UI](https://img.shields.io/badge/Web%20UI-React-61DAFB?logo=react&logoColor=black)](README#-web-interface)
[![Status](https://img.shields.io/badge/Status-Alpha-green)](OCR-MCP_MASTER_PLAN.md)

## 📋 Table of Contents

- [🎯 What is OCR-MCP?](#-what-is-ocr-mcp)
- [✨ Feature summary](#-feature-summary)
- [🚀 Quick Start](#-quick-start)
- [🛠️ Installation](#-installation)
- [🌐 Web Interface](#-web-interface)
- [📖 Usage Examples](#-usage-examples)
- [🔧 Configuration](#-configuration)
- [🧠 AI Models & OCR Engines](#-ai-models--ocr-engines)
- [🖼️ Image Preprocessing](#️-image-preprocessing)
- [📦 Packaging & Distribution](#-packaging--distribution)
- [🛠️ Development](#️-development)
- [📄 License](#-license)
- [🔍 Document Analysis](#-document-analysis)
- [📊 Quality Assessment](#-quality-assessment)
- [🔄 Workflows](#-workflows)
- [🔄 Format Conversion](#-format-conversion)
- [📷 Scanner Integration](#-scanner-integration)
- [📈 Performance & Benchmarks](#-performance--benchmarks)
- [🔍 API Reference](#-api-reference)
- [📚 Documentation](#-documentation)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

## What is OCR-MCP?

- **Web app** — React + FastAPI UI for people: upload or scan documents, pick OCR engine, get text/PDF/JSON. Ports 10858 (frontend) and 10859 (backend).
- **MCP server** — FastMCP 3.1 server for IDEs: Claude Desktop, Cursor, Windsurf, etc. Exposes OCR, preprocessing, scanner control, and workflows as tools. Sampling and agentic workflow (SEP-1577) supported.

**Agentic workflows:** Example prompt: *"Scan and analyze the document, then show me a formatted analysis."* The IDE agent chains MCP tools: e.g. list scanner → scan → OCR (chosen backend) → layout/analysis → then formats and returns the analysis doc.

### Features

**📥 Input Sources**: Direct scanner control, file upload, batch processing
**🖼️ Preprocessing**: Deskew, enhance, crop, rotate, noise reduction
**🔍 Analysis**: Layout detection, table extraction, form analysis, metadata
**📊 Quality**: OCR validation, backend comparison, confidence scoring
**🔄 Workflows**: Custom pipelines, intelligent routing, batch automation
**📄 Output**: Multiple formats (text, HTML, PDF, JSON, searchable PDFs)

### Automation

- **Auto-backend selection** per document
- **Quality-gated processing** with retries
- **Pipelines** and batch runs

#### Primary OCR Engines

**🚀 Mistral OCR 3 (December 2025)** - *State-of-the-Art Document Processing*
- **Performance**: 74% win rate over Mistral OCR 2 on forms, scanned docs, complex tables, handwriting.
- **Latency**: ~0.7s average processing time (OCR-2512 SOTA API).
- **Integration**: Dedicated SOTA OCR payload for high-fidelity Markdown extraction.
- **Capabilities**: Advanced handwriting recognition, form processing, scanned document handling, complex table reconstruction
- **Strengths**: Superior accuracy on enterprise document types, cost-effective at $2/1K pages, HTML table reconstruction
- **Repository**: https://mistral.ai/products/ocr
- **API**: https://mistral.ai/docs (mistral-ocr-2512 model)

**🔥 DeepSeek-OCR (October 2025)** - *Current State-of-the-Art*
- **Downloads**: 4.7M+ on Hugging Face (most downloaded OCR model)
- **Capabilities**: Vision-language OCR with advanced text understanding
- **Strengths**: Multilingual support, complex layouts, mathematical formulas
- **Repository**: https://huggingface.co/deepseek-ai/DeepSeek-OCR
- **Paper**: https://arxiv.org/abs/2510.18234

**🎯 Florence-2 (June 2024)** - *Removed in v0.3.0 — general vision model, not OCR specialist*
- Replaced by PaddleOCR-VL-1.5 which benchmarks at 94.5% vs Florence-2's stub implementation

**🐼 PaddleOCR-VL-1.5 (January 2026)** - *Current SOTA for Document Parsing*
- **Accuracy**: 94.5% on OmniDocBench v1.5 — #1 open-source at release
- **Architecture**: NaViT encoder + ERNIE-4.5-0.3B LM (0.9B params total)
- **Strengths**: Tables, formulas, charts, seals, irregular/tilted docs, 109 languages
- **VRAM**: ~3.3GB with flash-attn; install: `pip install flash-attn --no-build-isolation`
- **Repository**: https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5

**🔬 DeepSeek-OCR-2 (January 2026)** - *Visual Causal Flow Architecture*
- **Architecture**: Visual Causal Flow for context-aware document extraction
- **Strengths**: Clean structured markdown output, complex document layouts
- **Parameters**: 3B, ~8GB VRAM (bfloat16)
- **Repository**: https://huggingface.co/deepseek-ai/DeepSeek-OCR-2

**🎓 olmOCR-2 (October 2025)** - *Academic Document Specialist*
- **Built on**: Qwen2.5-VL-7B-Instruct with GRPO RL fine-tuning
- **Benchmark**: 82.4 on olmOCR-Bench (1,403 diverse PDF documents)
- **Strengths**: arXiv papers, LaTeX equations, multi-column academic layouts
- **Repository**: https://huggingface.co/allenai/olmOCR-2-7B-1025

**📊 DOTS.OCR (July 2025)** - *Document Table Specialist*
- **Focus**: Document layout analysis, table recognition, formula extraction
- **Repository**: https://huggingface.co/rednote-hilab/dots.ocr

**🏭 PP-OCRv5 (2025)** - *Industrial-Grade OCR (Legacy Pipeline)*
- **Strengths**: High throughput, CJK text, lightweight CPU deployment
- **Repository**: https://huggingface.co/PaddlePaddle/PP-OCRv5

**🎨 Qwen2.5-VL (December 2025)** - *Advanced Multimodal VLM*
- **Benchmark**: Near GPT-4o on DocVQA and MathVista, 90+ languages
- **Repository**: https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct

#### OCR Capabilities

- **Plain Text OCR**: Standard text extraction from images
- **Formatted Text OCR**: Preserves layout and formatting structure
- **Fine-Grained OCR**: Extract text from specific regions with coordinate precision
- **Multi-Crop OCR**: Process documents with complex layouts by dividing into regions
- **HTML Rendering**: Generate HTML output with visual layout preservation
- **Document Understanding**: Table extraction, formula recognition, layout analysis

#### Auto-Backend Selection

OCR-MCP automatically selects the best backend based on:
- **Document Type**: PDF, image, scanned document, or comic
- **Content Complexity**: Plain text vs. structured documents
- **Language Requirements**: Multilingual content detection
- **Performance Needs**: Speed vs. accuracy trade-offs

#### Advanced Document Pre-processing

**Qwen-Image-Layered** (optional) for image decomposition:

- **Layer Separation**: Decompose documents into independent RGBA layers (text, background, images, graphics)
- **Selective OCR**: Process text layers independently for improved accuracy on complex documents
- **Noise Reduction**: Isolate and remove background noise, watermarks, and interfering elements
- **Content Isolation**: Separate handwritten notes, stamps, and annotations from main text
- **Layout Preservation**: Maintain document structure while enabling targeted OCR processing
- **Multi-modal Enhancement**: Combine with traditional OCR for hybrid processing pipelines

#### Community & Industry Adoption

Current OCR landscape shows rapid evolution:
- **DeepSeek-OCR**: Leading community downloads, strong enterprise interest
- **PaddleOCR-VL-1.5**: January 2026 SOTA, 94.5% OmniDocBench — new reference point
- **DOTS.OCR**: Document processing industry standard
- **PP-OCRv5**: Production deployment in enterprise applications

## 🤖 AI Hardware Requirements

While basic Tesseract OCR runs on any CPU, advanced SOTA models have specific requirements:

- **Minimal (Tesseract/EasyOCR)**: Any CPU, 4GB RAM.
- **Recommended (PaddleOCR-VL-1.5/GOT-OCR2.0)**: NVIDIA RTX 3060+ (12GB VRAM). Requires flash-attn for PaddleOCR-VL.
- **High Performance (DeepSeek-OCR-2/olmOCR-2/Qwen)**: NVIDIA RTX 3090/4090 (24GB VRAM).

**Local Intelligence (LLM):**
- **Auto-Discovery**: The system automatically detects and uses running Ollama or LM Studio instances for semantic document analysis and classification.

> [!IMPORTANT]
> **GPU Usage**: SOTA models behave significantly better with CUDA acceleration. CPU fallback is available for most models but performance will be 10-50x slower.

## ✨ Feature summary

### Core OCR
- **10+ backends**: Mistral OCR, PaddleOCR-VL-1.5, DeepSeek-OCR-2, olmOCR-2, Qwen2.5-VL, GOT-OCR 2.0, DOTS.OCR (+ PP-OCRv5, EasyOCR, Tesseract legacy)
- **Auto backend selection** per document
- **Multiple Processing Modes**: Text, formatted, layout preservation, fine-grained extraction
- **Multi-language Support**: 80+ languages across all backends

### 🖼️ Advanced Image Preprocessing
- **Deskew**: Automatic text straightening with multiple algorithms
- **Enhancement**: Contrast, brightness, sharpness, noise reduction
- **Cropping**: Auto-detect content boundaries, manual coordinates
- **Rotation**: Auto-detect orientation, manual angle correction
- **Quality Pipeline**: Complete preprocessing workflow

### 🔍 Document Structure Analysis
- **Layout Detection**: Headers, paragraphs, columns, sections
- **Table Extraction**: Structured data from complex tables
- **Form Analysis**: Checkbox, text field, signature detection
- **Reading Order**: Logical text flow determination
- **Document Classification**: Auto-detect document types

### 📊 Quality Assessment & Validation
- **OCR Accuracy Scoring**: Character, word, and sequence accuracy
- **Backend Comparison**: Performance analysis across engines
- **Confidence Analysis**: Detailed confidence metrics and thresholds
- **Ground Truth Validation**: Compare against known correct text
- **Quality Recommendations**: Automated improvement suggestions

### 🔄 Intelligent Workflow Automation
- **Custom Pipeline Builder**: Drag-and-drop workflow creation
- **Quality Gates**: Conditional processing based on results
- **Batch Orchestration**: Concurrent processing with progress tracking
- **Error Recovery**: Automatic retry with fallback strategies
- **Resource Optimization**: Intelligent load balancing

### 🔄 Format conversion
- **PDF Processing**: Extract images, create searchable PDFs
- **Image Conversion**: Format conversion with quality control
- **Document Assembly**: Combine images into PDFs
- **Searchable PDFs**: OCR text embedded as invisible layers
- **Multi-format Export**: Text, HTML, JSON, XML, Word

### 📷 Scanner
- **WIA Support**: Direct Windows scanner control
- **Device Discovery**: Auto-detect connected scanners
- **Advanced Settings**: DPI, color modes, paper sizes, brightness/contrast
- **Batch Scanning**: ADF support with page separation
- **Preview Mode**: Positioning and cropping verification

#### Web interface

The OCR-MCP web interface is accessible at:
- **URL**: `http://localhost:8765`
- **Dashboard**: Real-time monitoring of all OCR and scanner operations
- **Scanner Control**: Direct hardware acquisition with live preview
- **Batch Processing**: Parallel document processing with progress tracking
- **Scanner**: WIA 2.0 (Windows).

## 🏗️ Architecture

### AI Models & OCR Engines

#### Backends (10+)
🐼 **[PaddleOCR-VL-1.5](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5)** - Jan 2026 SOTA, 94.5% OmniDocBench, 0.9B params
🔬 **[DeepSeek-OCR-2](https://huggingface.co/deepseek-ai/DeepSeek-OCR-2)** - Visual Causal Flow, Jan 2026, 3B params
🎓 **[olmOCR-2](https://huggingface.co/allenai/olmOCR-2-7B-1025)** - Academic PDFs, math equations, Oct 2025, 7B
🚀 **[Mistral OCR](https://mistral.ai)** - Cloud API, 94.9% accuracy, Dec 2025
🖼️ **[Qwen2.5-VL](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)** - Multimodal VLM, DocVQA near GPT-4o
🎯 **[GOT-OCR 2.0](https://github.com/Ucas-HaoranWei/GOT-OCR2.0)** - Fast, lean (580M), mixed content
🚀 **[DeepSeek-OCR](https://huggingface.co/deepseek-ai/DeepSeek-OCR)** - Original, cloud API
📊 **[DOTS.OCR](https://huggingface.co/rednote-hilab/dots.ocr)** - Table and document structure specialist

#### Legacy/Compatibility Models
📖 **[Tesseract OCR](https://github.com/tesseract-ocr/tesseract)** - Classic open-source OCR engine, CPU backstop
🔤 **[EasyOCR](https://github.com/JaidedAI/EasyOCR)** - GPU-accelerated, 80+ languages, handwriting
🏭 **[PP-OCRv5](https://huggingface.co/PaddlePaddle/PP-OCRv5)** - Industrial PaddlePaddle pipeline

#### Model Capabilities Matrix

| Model | Text OCR | Tables | Formulas | Handwriting | Multi-lang | VRAM | Speed |
|-------|----------|--------|----------|-------------|------------|------|-------|
| **PaddleOCR-VL-1.5** | ✅ | ✅ | ✅ | ✅ | 109 langs | 3.3GB* | Fast |
| **DeepSeek-OCR-2** | ✅ | ✅ | ✅ | ⚠️ | ✅ | ~8GB | Medium |
| **olmOCR-2** | ✅ | ✅ | ✅ | ⚠️ | ✅ | ~16GB | Slow |
| Mistral OCR | ✅ | ✅ | ✅ | ✅ | ✅ | 0 (API) | Fast |
| Qwen2.5-VL | ✅ | ✅ | ✅ | ✅ | ✅ | ~16GB | Slow |
| GOT-OCR 2.0 | ✅ | ✅ | ✅ | ✅ | ✅ | ~2GB | Medium |
| DOTS.OCR | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ~6GB | Fast |
| PP-OCRv5 | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | low | Very Fast |
| EasyOCR | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | low | Medium |
| Tesseract | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | 0 | Very Fast |

*\* PaddleOCR-VL-1.5 requires `flash-attn` for 3.3GB; without it ~40GB (OOM on 24GB GPU)*

See [AI_MODELS.md](AI_MODELS.md) for details and benchmarks.

### Portmanteau Tool Ecosystem (2026 SOTA)

#### Document Processing
**`document_processing(operation, ...)`** - OCR, analysis, quality assessment
- process_document, process_batch, analyze_layout, extract_tables, detect_forms
- analyze_reading_order, classify_type, extract_metadata
- assess_quality, validate_accuracy, compare_backends, analyze_image_quality

#### Image Management
**`image_management(operation, ...)`** - Preprocessing and format conversion
- preprocess (deskew, denoise, grayscale, threshold, autocrop)
- convert (PNG, JPG, TIFF, WebP)
- pdf_to_images, embed_text (searchable PDF)

#### Scanner Operations (WIA, Windows)
**`scanner_operations(operation, ...)`** - Scanner hardware control
- list_scanners, scanner_properties, configure_scan
- scan_document, scan_batch, preview_scan, diagnostics

#### Workflow Management
**`workflow_management(operation, ...)`** - Batch and pipeline orchestration
- process_batch_intelligent, create_processing_pipeline, execute_pipeline
- monitor_batch_progress, optimize_processing
- ocr_health_check, list_backends, manage_models

#### Help & Status
**`help(level, topic?)`** - basic | intermediate | advanced
**`status(level)`** - basic | detailed

### WebApp Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Web Interface                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │ Single  │  │   Batch    │  │  Image     │  │   Doc    │  │
│  │ Upload  │  │ Processing │  │  Preproc   │  │ Analysis │  │
│  └─────────┘  └────────────┘  └────────────┘  └──────────┘  │
│  ┌─────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │ Quality │  │ Workflows  │  │ Conversion │  │ Scanner  │  │
│  │ Assess  │  │ & Pipelines│  │ & Export   │  │ Control  │  │
│  └─────────┘  └────────────┘  └────────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────┤
│                 FastMCP Server (20+ Tools)                  │
├─────────────────────────────────────────────────────────────┤
│   OCR Engines ┌──┬──┬──┬──┬──┬──┬──┐  Document Processing   │
│               │M │D │F │D │P │Q │E │  Image Analysis        │
│               │3 │S │2 │O │P │I │O │  Quality Assessment    │
│               └──┴──┴──┴──┴──┴──┴──┘  Workflow Automation   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Installation

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/) (recommended). GPU optional for SOTA models.

### From repo (recommended)

```powershell
# Clone (or open repo)
cd D:\Dev\repos\ocr-mcp

# Install deps
uv sync

# Run MCP server (stdio)
just run
# or: uv run ocr-mcp
```

### One-liner (no clone)

```powershell
uvx ocr-mcp
```
Requires [ocr-mcp on PyPI](https://pypi.org/project/ocr-mcp/) or `uvx --from . ocr-mcp` from repo root.

### Claude Desktop / MCP clients

Add to `claude_desktop_config.json` (or your client’s MCP config):

**With uv (from repo):**
```json
"mcpServers": {
  "ocr-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/ocr-mcp", "run", "ocr-mcp"]
  }
}
```

**With Python (after `uv sync` or `pip install -e .`):**
```json
"ocr-mcp": {
  "command": "python",
  "args": ["-m", "ocr_mcp.server"],
  "env": {
    "OCR_CACHE_DIR": "C:/path/to/cache",
    "OCR_DEVICE": "cuda"
  }
}
```

Replace `D:/Dev/repos/ocr-mcp` with your repo path. Optional env: `OCR_CACHE_DIR`, `OCR_DEVICE` (cuda/cpu/auto).

### Web UI

React + FastAPI app in `web_sota/`. Frontend 10858, backend 10859.

```powershell
just webapp
```
Opens backend + Vite; then open http://localhost:10858. Or from `web_sota/`: `npm install`; start backend (from project root: `uv run uvicorn backend.app:app --port 10859`), then `npm run dev -- --port 10858`.

## 🌐 Web Interface

React + FastAPI app: upload, preprocess, OCR, batch, scanner. Run with `just webapp` or see [Installation](#-installation).

### Overview

- Upload (drag-drop), preprocessing, OCR with backend choice, results (text/JSON/HTML)
- Batch processing with progress
- Scanner control (WIA)
- Pipelines and quality checks

### 📱 Interface Sections

#### Single document
1. Upload (drag-drop)
2. Preprocess (deskew, enhance, crop)
3. OCR (pick backend)
4. Results (text, JSON, HTML, PDF)

**Features:**
- Real-time processing status with progress bars
- Quality score display (A-F grading system)
- Confidence metrics and accuracy analysis
- Export to 6+ formats (Text, JSON, HTML, PDF, Word, XML)

#### 📦 **Intelligent Batch Processing**
**Smart Multi-Document Processing:**
- **Strategy Selection**: Auto, Quality-Focused, Speed, Custom Pipeline
- **Quality Gates**: Configurable thresholds with automatic retries
- **Progress Dashboard**: Real-time status for up to hundreds of documents
- **Concurrent Processing**: Optimized resource utilization
- **Results Aggregation**: Summary statistics and error reporting

**Dashboard Features:**
- Individual document status tracking
- Success/failure rates and time estimates
- Quality distribution analysis
- Bulk export and reporting tools

#### 🖼️ **Image Preprocessing Studio**
**Professional Image Enhancement:**
- **Visual Editor**: Before/after comparison with split-view
- **Tool Palette**: Deskew, enhance, crop, rotate with live preview
- **Quality Analysis**: Automatic assessment of improvement effectiveness
- **Batch Processing**: Apply pipelines to multiple images
- **Parameter Control**: Fine-grained adjustment of all enhancement settings

#### 🔍 **Document Analysis Lab**
**Advanced Structure Detection:**
- **Layout Analysis**: Header/footer detection, column identification
- **Table Extraction**: Structured data from complex table layouts
- **Form Detection**: Checkbox, text field, signature recognition
- **Reading Order**: Logical text flow determination
- **Type Classification**: Auto-document type identification
- **Metadata Extraction**: Dates, names, numbers, addresses

#### 📊 **Quality Assessment Center**
**OCR Validation & Optimization:**
- **Single Assessment**: Comprehensive quality scoring for individual results
- **Backend Comparison**: Performance analysis across all OCR engines
- **Accuracy Validation**: Ground truth comparison with detailed metrics
- **Image Quality Check**: Pre-OCR quality analysis and recommendations
- **Confidence Analysis**: Detailed confidence scoring and error patterns

#### 🔄 **Custom Pipeline Builder**
**Workflow Orchestration:**
- **Visual Designer**: Drag-and-drop pipeline creation
- **Step Library**: All 20+ tools as reusable components
- **Conditional Logic**: Quality gates and decision branches
- **Template System**: Pre-built pipelines for common scenarios
- **Execution Monitoring**: Real-time pipeline progress and debugging

#### 📷 **Scanner Control Center**
**Professional Scanning:**
- **Device Discovery**: Auto-detection of WIA-compatible scanners
- **Advanced Settings**: DPI, color modes, paper sizes, brightness/contrast
- **Preview Mode**: Positioning verification before final scan
- **Batch Scanning**: ADF support with automatic page separation
- **Integration**: Seamless workflow connection to OCR processing

### 🔧 **Technical Architecture**

#### Frontend Stack
- **Vanilla JavaScript**: No heavy frameworks, fast loading
- **Modern CSS**: Grid, Flexbox, CSS Variables, Animations
- **Responsive Design**: Mobile-first approach
- **Progressive Enhancement**: Works without JavaScript
- **Accessibility**: WCAG 2.1 AA compliance

#### Backend Integration
- **FastAPI Server**: Async processing with automatic MCP server management
- **RESTful API**: Clean endpoints for all functionality
- **Real-time Updates**: WebSocket-based progress monitoring
- **File Security**: Secure temporary file handling
- **Error Recovery**: Comprehensive error handling and user feedback

#### Performance Optimizations
- **Lazy Loading**: Components load on demand
- **Background Processing**: Non-blocking operations
- **Smart Caching**: Results caching to avoid redundant processing
- **Resource Management**: Intelligent memory and CPU utilization
- **Progressive Rendering**: Fast initial load with incremental enhancement

### 🎯 **User Experience Highlights**

#### **Smart Defaults**
- Intelligent backend selection based on document type
- Automatic preprocessing pipeline recommendations
- Quality threshold suggestions per document type

#### **Guided Workflows**
- Step-by-step processing guidance
- Contextual help and tooltips
- Progressive disclosure of advanced options

#### **Quality Assurance**
- Real-time quality metrics during processing
- Automatic suggestions for improvement
- Validation against quality thresholds

#### **Batch Intelligence**
- Optimal concurrent processing limits
- Automatic retry on failures
- Quality-based prioritization

#### **Export Flexibility**
- Multiple format support with one-click conversion
- Bulk export capabilities
- Custom export profiles

### 📊 **Monitoring & Analytics**

#### **System Health**
- Real-time backend availability status
- Resource utilization monitoring
- Performance metrics dashboard

#### **Processing Analytics**
- Success/failure rate tracking
- Average processing times by backend
- Quality score distributions

#### **Batch Monitoring**
- Individual document status
- Overall progress visualization
- Error pattern analysis

### 🔒 **Security & Privacy**

- **File Security**: Secure temporary file handling with automatic cleanup
- **No External Calls**: All processing happens locally
- **Data Privacy**: No document content sent to external services
- **Local Processing**: Complete offline capability
- **Audit Trail**: Processing history and error logging

## 💡 Usage Examples

### Basic OCR Processing

```python
# Auto-select best available backend
result = await document_processing(
    operation="process_document",
    source_path="/path/to/document.png"
)
print(result["text"])  # Extracted text
```

### Formatted OCR with HTML Output

```python
# DeepSeek-OCR formatted text preservation
result = await document_processing(
    operation="process_document",
    source_path="/path/to/scanned_page.png",
    backend="deepseek-ocr",
    ocr_mode="format",
    output_format="html"
)
# Returns: HTML with preserved layout and formatting
```

### Fine-grained Region Extraction

```python
# Extract text from specific coordinates
result = await document_processing(
    operation="extract_regions",
    source_path="/path/to/document.png",
    region=[100, 200, 400, 300]  # [x1,y1,x2,y2]
)
# Returns: Structured text extraction by region
```

### Batch Processing

```python
# Process multiple documents
results = await workflow_management(
    operation="process_batch_intelligent",
    document_paths=[
        "/path/to/doc1.png",
        "/path/to/doc2.png",
        "/path/to/doc3.png"
    ],
    workflow_type="auto",
    quality_threshold=0.8
)
# Returns: Intelligent batch processing with quality control
```

## 🎨 Advanced Features

### Document Layout Analysis

```python
# Analyze document structure
layout = await document_processing(
    operation="analyze_layout",
    source_path="/path/to/complex_document.png",
    analysis_type="comprehensive",
    detect_tables=True,
    detect_forms=True
)
# Returns: Detected tables, columns, headers, text blocks
```

### Multi-Backend Comparison

```python
# Compare OCR accuracy across backends
comparison = await document_processing(
    operation="compare_backends",
    source_path="/path/to/test_image.png",
    backends=["paddleocr-vl", "deepseek-ocr2", "got-ocr"]
)
# Returns: Accuracy scores, processing times, confidence metrics
```

### Image Preprocessing

```python
# Enhance image quality for better OCR
enhanced = await image_management(
    operation="preprocess",
    image_path="/path/to/skewed_document.png",
    operations=["deskew", "enhance", "crop"]
)
# Returns: Preprocessed image optimized for OCR
```

## 🔧 Configuration Options

### Environment Variables

- **`OCR_CACHE_DIR`**: Model cache directory (default: `~/.cache/ocr-mcp`)
- **`OCR_DEVICE`**: Computing device (`cuda`, `cpu`, `auto`)
- **`OCR_MAX_MEMORY`**: Maximum GPU memory usage in GB
- **`OCR_DEFAULT_BACKEND`**: Default OCR backend (`got-ocr`, `tesseract`, etc.)
- **`OCR_BATCH_SIZE`**: Default batch processing size

### Backend-Specific Settings

```yaml
# config/ocr_config.yaml
backends:
  got_ocr:
    model_size: "base"  # or "large"
    cache_dir: "/models/got-ocr"
    device: "cuda:0"

  tesseract:
    language: "eng+fra+deu"
    config: "--psm 6"

  easyocr:
    languages: ["en", "fr", "de"]
    gpu: true
```

## 📊 Performance Benchmarks

### Published Benchmark Scores (2025–2026)

| Backend | OmniDocBench v1.5 | olmOCR-Bench | Claimed Accuracy | Notes |
|---------|-------------------|--------------|-----------------|-------|
| **PaddleOCR-VL-1.5** | **94.5%** | — | — | Jan 2026 SOTA |
| **Mistral OCR** | — | — | 94.9% | Dec 2025, API |
| **DeepSeek-OCR-2** | — | — | — | Jan 2026, not benchmarked yet |
| **olmOCR-2** | — | **82.4** | — | Oct 2025 |
| GOT-OCR2.0 | — | — | 97.2% clean text | Internal |
| Tesseract | — | — | 78–85% | Classic |

### Speed Reference (RTX 4090)

| Backend | Approx. docs/min | VRAM |
|---------|-----------------|------|
| PaddleOCR-VL-1.5 | ~100 | 3.3GB |
| GOT-OCR2.0 | ~200 | ~2GB |
| DeepSeek-OCR-2 | ~60 | ~8GB |
| olmOCR-2 | ~30 | ~16GB |
| PP-OCRv5 | ~300 | low |
| Tesseract | ~200 | 0 |

## 🛠️ Development Status

- ✅ **Planning**: Complete master plan and architecture
- ✅ **Phase 1**: Core infrastructure (Completed)
- ✅ **Phase 2**: Multi-backend OCR support (Completed)
- ✅ **Phase 3**: Web interface (done)
- ✅ **Phase 4**: Advanced document processing (Completed)
- ✅ **Phase 5**: Scanner integration (Completed)
- 🟡 **Phase 6**: Production deployment and optimization (Alpha Release)
- 🔄 **Phase 7**: Beta testing and community feedback (Next)
- 🔄 **Phase 8**: Production release preparation (Future)

### ✅ **Completed Features**
- **FastMCP 3.1 Integration**: State-of-the-art MCP server with conversational features
- **10 OCR Backends**: PaddleOCR-VL-1.5, DeepSeek-OCR-2, olmOCR-2, Mistral OCR, DeepSeek-OCR, DOTS.OCR, Qwen2.5-VL, GOT-OCR 2.0, EasyOCR, Tesseract
- **Professional React Webapp**: Complete TypeScript frontend with modern UI/UX
- **Intelligent Backend Selection**: Automatic model routing based on document analysis
- **Document Processing Pipeline**: Multi-stage OCR with quality assessment
- **Advanced Image Preprocessing**: Real-time enhancement with visual feedback
- **Scanner Integration**: Direct WIA hardware control for Windows scanners
- **Batch Processing**: Concurrent document processing with progress monitoring
- **Quality Assessment**: OCR validation with accuracy metrics and recommendations
- **Format Conversion**: Export to PDF, Word, JSON, HTML, and searchable PDFs
- **Comprehensive Error Handling**: Structured errors with recovery suggestions
- **Cross-Platform Support**: Windows and Linux with appropriate abstractions
- **Complete Documentation**: AI models guide, technical specifications, testing framework

See [OCR-MCP_MASTER_PLAN.md](OCR-MCP_MASTER_PLAN.md) for detailed roadmap.

## 📚 Documentation

### Docs

- [AI_MODELS.md](AI_MODELS.md) – backends, benchmarks
- [OCR-MCP_MASTER_PLAN.md](OCR-MCP_MASTER_PLAN.md) – architecture, roadmap
- [tests/README.md](tests/README.md) – testing

### 🛠️ Development Resources

- **API Documentation**: http://localhost:10859/docs (when backend is running)
- **Health Monitoring**: http://localhost:10859/api/health
- **Interactive API Explorer**: Full Swagger UI with live testing

### 📋 Quick Reference

| Resource | Purpose | Location |
|----------|---------|----------|
| AI Models Guide | Model specifications & benchmarks | [AI_MODELS.md](AI_MODELS.md) |
| Technical Architecture | System design & roadmap | [OCR-MCP_MASTER_PLAN.md](OCR-MCP_MASTER_PLAN.md) |
| Testing Framework | Test execution & validation | [tests/README.md](tests/README.md) |
| API Documentation | Interactive API explorer | http://localhost:10859/docs |
| Health Monitoring | System status & diagnostics | http://localhost:10859/api/health |

## 🤝 Integration with Existing MCP Servers

### CalibreMCP Integration

OCR-MCP enhances CalibreMCP's OCR capabilities:

```python
# CalibreMCP can now use OCR-MCP for advanced processing
result = await calibre_ocr(
    source="/path/to/scanned_book.pdf",
    provider="ocr-mcp",  # New option!
    mode="format",
    render_html=True
)
```

### Document Processing Workflows

- **Research Papers**: Extract structured text from academic PDFs
- **Receipt Processing**: Automated data extraction from scanned receipts
- **Book Digitization**: High-quality OCR for scanned books
- **Accessibility**: Convert images to readable text for screen readers

## 📈 Roadmap

### ✅ Completed Milestones
- [x] FastMCP 3.1 Core Infrastructure
- [x] GOT-OCR2.0 Multi-mode Integration
- [x] Robust WIA 2.0 Hardware Integration (Canon LiDE 400 verified)
- [x] React web interface
- [x] Mistral OCR 3 (OCR-2512) SOTA Backend Implementation
- [x] Multi-format Pipeline (PDF, CBZ, Scanned Docs)

### Immediate (Next 2-4 weeks)
- [ ] Performance Benchmarking Suite
- [ ] Advanced Image Preprocessing (Deskew/Enhance)
- [ ] TWAIN Backend Support
- [ ] Multi-language Model Fine-tuning

### Medium-term (2-3 months)
- [ ] Advanced Layout Intelligence (Panel analysis for Manga)
- [ ] Batch processing concurrency optimizations
- [ ] Cloud deployment (Docker/Kubernetes)
- [ ] Mobile scanning workflow integration

## 🤝 Contributing

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/ocr-mcp.git
   cd ocr-mcp
   ```

2. **Install Poetry** (if not already installed)
   ```bash
   pip install poetry
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Set up development environment** (recommended)
   ```bash
   poetry run ocr-mcp-setup-dev
   # This installs pre-commit hooks and sets up the environment
   ```

### 📦 Packaging & Distribution

This repository is SOTA 2026 compliant and uses the officially validated `@anthropic-ai/mcpb` workflow for distribution.

#### Pack Extension
To generate a `.mcpb` distribution bundle with complete source code and automated build exclusions:
```bash
# SOTA 2026 standard pack command
mcpb pack . dist/ocr-mcp.mcpb
```

#### Discovery & listings
- **Glama.ai**: Use the [glama.json](glama.json) snippet in your MCP client config; includes FastMCP 3.1, sampling, agentic, prompts. [Submit/update](https://glama.ai/mcp/servers) on Glama for discovery.
- **LLM discoverability**: [llms.txt](llms.txt) at repo root gives LLMs and crawlers a short sitemap (README, CHANGELOG, AI models, install, listings).
- **Justfile (just)**: [justfile](justfile) follows the [justfiles standard](https://github.com/casey/just). Run `just` to list recipes; `just run`, `just test`, `just webapp`, `just install`, `just pack`, etc.

---

## 🛠️ Development

5. **Run tests:** `just test` or `uv run pytest`
6. **Lint/format:** `just lint`, `just format`
7. **Web UI:** `just webapp` or see Web UI above

### Pre-commit Hooks

This project uses pre-commit hooks to maintain code quality. The following tools are automatically run on each commit:

- **Ruff**: Fast Python linter, formatter, and import sorter
- **MyPy**: Type checker
- **Bandit**: Security linter
- **Detect-secrets**: Secret detection
- **Markdownlint**: Markdown linter

To manually run all checks:
```bash
poetry run pre-commit run --all-files
```

OCR-MCP welcomes contributions! Areas of particular interest:

- **New OCR Backends**: Integration of additional OCR engines
- **Performance Optimization**: GPU memory management, batch processing
- **Specialized Models**: Domain-specific OCR improvements
- **Documentation**: Usage examples, integration guides
- **Testing**: Comprehensive test coverage and benchmarks

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **GOT-OCR2.0 Team** (UCAS): Revolutionary OCR model that inspired this project

---

See [OCR-MCP_MASTER_PLAN.md](OCR-MCP_MASTER_PLAN.md) for architecture and roadmap.
