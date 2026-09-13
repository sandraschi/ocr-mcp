# ocr-mcp (MCPB Bundle)

FastMCP server providing comprehensive OCR capabilities to the MCP ecosystem

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "ocr-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "ocr_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **main_stdio**: main(stdio)
- **main_http**: main(http)
- **main_sse**: main(sse)
- **register_prefab_tools**: Register Prefab UI tools with the FastMCP app.
- **show_health_card**: show_health_card
- **show_backends_card**: show_backends_card
- **execute_agentic_workflow**: execute_agentic_workflow
- **ingest_book**: ingest_book
- **process_document**: process_document
- **manage_image**: manage_image
- **operate_scanner**: operate_scanner
- **manage_workflow**: manage_workflow
- **manage_corpus**: manage_corpus
- **get_help**: get_help
- **get_status**: get_status
- **shutdown_server**: shutdown_server
- **register_sota_tools_comprehensive**: register_sota_tools(comprehensive)
- **register_sota_tools_basic**: register_sota_tools(basic)
- **register_sota_tools_layout**: register_sota_tools(layout)

## Requirements

- Python 3.12+
- uv
