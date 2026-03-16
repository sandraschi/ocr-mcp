"""
Scanner tools compatibility layer.

Scanner operations are consolidated in ocr_tools.scanner_operations (portmanteau).
This module provides legacy aliases for tests that import register_scanner_tools
or register_scanner_operations_tools.
"""

from .ocr_tools import register_sota_tools

register_scanner_tools = register_sota_tools
register_scanner_operations_tools = register_sota_tools
