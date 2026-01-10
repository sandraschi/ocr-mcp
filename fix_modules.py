import os
import re


def fix_module(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    # Fix the corrupted keywords
    # Based on the pattern: line[4:] was applied to lines that didn't have 4 leading spaces

    # Common corruptions:
    # "async def" -> "c def" (if it had 0 spaces and was sliced [4:]) -- wait.
    # "async def" is 9 chars. [4:] is "c def".
    # "def " is 4 chars. [4:] is "" (empty).
    # "Operation" is 9 chars. [4:] is "ation".

    # It's better to just RESTORE the file if I can, but I don't have backups.
    # I will attempt to fix the most obvious ones.

    content = content.replace("c def ", "async def ")
    content = content.replace("nc def ", "async def ")  # maybe?
    content = content.replace(
        "eration handler functions", "Operation handler functions"
    )
    content = content.replace(
        "iginal individual tool functions", "Original individual tool functions"
    )
    content = content.replace("\nasync def ", "\nasync def ")  # just in case

    # Let's also fix the indentation issue properly.
    # Actually, I should probably just re-read the files and unindent ONLY if they have 4 spaces.

    with open(filepath, "w") as f:
        f.write(content)


modules = [
    "src/ocr_mcp/tools/_analysis.py",
    "src/ocr_mcp/tools/_quality.py",
    "src/ocr_mcp/tools/_image.py",
    "src/ocr_mcp/tools/_conversion.py",
    "src/ocr_mcp/tools/_scanner.py",
    "src/ocr_mcp/tools/_workflow.py",
]

for mod in modules:
    print(f"Fixing {mod}...")
    fix_module(mod)
