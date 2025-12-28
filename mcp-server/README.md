# OCR-MCP: Claude Desktop Integration

**Advanced Document Processing Server for Claude Desktop**

OCR-MCP provides state-of-the-art OCR capabilities directly within Claude Desktop, enabling seamless document understanding and processing through natural language interaction.

## 🎯 What is OCR-MCP?

OCR-MCP is a FastMCP server that integrates multiple cutting-edge OCR engines to provide comprehensive document processing capabilities. It processes various document formats, controls scanner hardware, and delivers results in multiple output formats.

### Key Features

- **Multiple OCR Backends**: DeepSeek-OCR, Florence-2, PP-OCRv5, GOT-OCR2.0, Tesseract
- **Document Format Support**: PDF, CBZ/CBR archives, PNG, JPG, TIFF, BMP
- **Scanner Integration**: Direct WIA control for Windows scanners
- **Batch Processing**: Concurrent processing of multiple documents
- **Output Formats**: Text, HTML, Markdown, JSON, XML
- **Region Extraction**: Fine-grained text extraction from image areas

## 🚀 Installation

1. **Install Dependencies** (required before using OCR-MCP):
   ```bash
   pip install torch>=2.0.0 transformers>=4.35.0 pillow>=10.0.0
   pip install fastmcp>=2.14.1 opencv-python>=4.8.0 pytesseract>=0.3.10
   pip install easyocr>=1.7.0
   ```

2. **Install OCR-MCP**:

   **For Claude Desktop (MCPB):**
   - Download the `ocr-mcp-[version].mcpb` file
   - Drag and drop it into Claude Desktop settings
   - Claude Desktop will automatically install and configure the server

   **For Glama Client:**
   - Clone the repository: `git clone https://github.com/sandr/ocr-mcp.git`
   - Install dependencies: `pip install -e .`
   - Glama will automatically detect the `glama.json` configuration
   - The server will be available in Glama's MCP server list

## 📖 Usage

Once installed, you can interact with OCR-MCP through natural language:

### Basic Document Processing
```
Extract text from this PDF: /path/to/document.pdf
Process this scanned image: photo.jpg
```

### Scanner Operations
```
List my available scanners
Scan a document and save it as scanned.png
```

### Batch Processing
```
Process these documents: doc1.pdf, doc2.jpg, doc3.png
Convert all PDFs in /documents/ to markdown
```

### Advanced Features
```
Extract text from the top section of this image
Use DeepSeek-OCR for this complex document
Check which OCR backends are available
```

## 🔧 Configuration

Configure OCR-MCP through Claude Desktop settings:

- **API Key**: For Mistral OCR backend (optional)
- **Default Backend**: Preferred OCR engine (auto/deepseek/florence/ppocr/tesseract/got/dots)
- **Scanner Timeout**: Timeout for scanner operations (default: 30 seconds)
- **Batch Concurrency**: Number of concurrent operations (default: 4)

## 🧠 OCR Backends

| Backend | Status | Best For |
|---------|--------|----------|
| DeepSeek-OCR | ✅ Available | Complex documents, math formulas, multilingual |
| Florence-2 | ✅ Available | Layout understanding, scene text |
| PP-OCRv5 | ✅ Available | Industrial OCR, high-volume processing |
| GOT-OCR2.0 | ✅ Available | Enhanced multimodal OCR |
| Tesseract | ✅ Available | Simple text, fallback option |
| Mistral OCR | ⚠️ API Key Required | Enterprise documents, handwriting |

## 📷 Scanner Support

OCR-MCP supports Windows scanners through WIA (Windows Image Acquisition):

- **Flatbed scanners**
- **Document feeders**
- **All-in-one devices**
- **Configurable resolution** (75-2400 DPI)
- **Color/grayscale modes**

## 📚 Document Formats

- **PDF**: Single and multi-page documents
- **Images**: PNG, JPG, TIFF, BMP
- **Archives**: CBZ, CBR comic book formats
- **Batch processing**: Multiple files concurrently

## 🎨 Output Formats

- **Text**: Plain text extraction
- **HTML**: Structured HTML with formatting
- **Markdown**: Markdown with headers and structure
- **JSON**: Structured data with metadata
- **XML**: XML format for system integration

## 🔍 Advanced Features

- **Region extraction**: Extract text from specific image areas
- **Confidence scoring**: Quality assessment for OCR results
- **Backend selection**: Choose optimal OCR engine per document
- **Progress tracking**: Real-time processing status
- **Error recovery**: Automatic fallback to alternative backends

## 🐛 Troubleshooting

### Backend Issues
If OCR backends are unavailable:
1. Check installation: `pip install -r requirements.txt`
2. Verify model downloads: Run the model installation script
3. Check backend status: Ask "which backends are available?"

### Scanner Problems
If scanners aren't detected:
1. Ensure scanner is powered on and connected
2. Install scanner drivers from manufacturer
3. Try different USB ports
4. Check Windows Device Manager

### Performance Issues
For slow processing:
1. Use batch processing for multiple documents
2. Select appropriate backend for document type
3. Reduce image resolution if not needed
4. Check available system memory

## 🤝 Support

- **Documentation**: See the prompts in Claude Desktop for detailed usage
- **Examples**: Extensive examples available in the prompts
- **Configuration**: All settings configurable through Claude Desktop
- **Updates**: New backends and features added regularly

## 📄 License

MIT License - See LICENSE file for details.

---

**OCR-MCP is built with FastMCP 2.14.1+ for optimal Claude Desktop integration.**