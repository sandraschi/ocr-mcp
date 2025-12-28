# OCR-MCP User Interaction Guide

## Getting Started

OCR-MCP is your document understanding companion. Here are the most common ways to interact with it:

## Basic Document Processing

### Process a Single Document
```
I have a PDF document at /path/to/document.pdf that I need to extract text from.
```
→ OCR-MCP will automatically select the best OCR backend and process the document.

### Process Images
```
Extract text from this image: /path/to/photo.jpg
```
→ Works with PNG, JPG, TIFF, BMP formats.

## Scanner Operations

### Check Available Scanners
```
What scanners do I have available?
```
→ Lists all connected scanner devices.

### Scan a Document
```
Scan a document using my default scanner and save it as scanned_document.png
```
→ Automatically detects and uses the default scanner.

### Advanced Scanning
```
Scan a high-resolution document at 600 DPI and save to /documents/scanned.pdf
```
→ Configurable resolution and output formats.

## Batch Processing

### Process Multiple Documents
```
Process these documents: invoice.pdf, contract.pdf, receipt.jpg
```
→ Concurrent processing for efficiency.

### Batch with Specific Output
```
Convert these PDFs to markdown format: doc1.pdf, doc2.pdf, doc3.pdf
```
→ Output in Text, HTML, Markdown, JSON, or XML.

## Advanced Features

### Extract Specific Regions
```
Extract text from the top-left corner of this image, about 200x100 pixels starting at position 50,50
```
→ Fine-grained text extraction from image regions.

### Check Backend Status
```
Which OCR backends are currently available?
```
→ Shows status of all OCR engines.

## Configuration

### Set Preferences
```
Use Florence-2 as my default OCR backend
```
→ Configure default backend preference.

### API Configuration
```
Set my Mistral OCR API key to: sk-your-api-key-here
```
→ Configure API keys for cloud backends.

## Common Use Cases

### Document Digitization
1. "Scan this paper document"
2. "Convert the scanned image to searchable text"
3. "Save the extracted text as a markdown file"

### Form Processing
1. "Process this filled form: form.pdf"
2. "Extract the handwritten text from the signature field"
3. "Validate the extracted data against expected formats"

### Archive Processing
1. "Process all PDFs in the /documents/archive/ folder"
2. "Convert them to markdown format"
3. "Save results to /processed_documents/"

### Research Papers
1. "Extract text from this academic paper: research.pdf"
2. "Focus on the abstract and conclusion sections"
3. "Save with high accuracy using DeepSeek-OCR backend"

## Troubleshooting

### Backend Issues
```
Why isn't the DeepSeek backend working?
```
→ Check backend status and installation.

### Scanner Problems
```
My scanner isn't detected
```
→ Verify scanner connection and drivers.

### File Format Issues
```
This PDF isn't processing correctly
```
→ Check file format and try alternative backends.

## Best Practices

1. **Choose the right backend** for your document type
2. **Use batch processing** for multiple documents
3. **Check backend status** before important operations
4. **Configure API keys** for cloud backends when needed
5. **Verify scanner connectivity** before scanning operations

## Output Formats

OCR-MCP supports multiple output formats:
- **Text**: Plain text extraction
- **HTML**: Structured HTML with formatting
- **Markdown**: Markdown with headers and lists
- **JSON**: Structured data with metadata
- **XML**: XML format for integration

## Performance Tips

- Use batch processing for efficiency
- Select appropriate backends for document types
- Monitor processing times and adjust concurrency
- Consider file sizes for optimal performance
- Use region extraction to focus on specific areas