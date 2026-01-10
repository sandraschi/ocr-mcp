import os
import re


def refactor_module(filepath):
    with open(filepath, "r") as f:
        lines = f.readlines()

    new_lines = []
    in_wrapper = False

    for line in lines:
        # Detect start of register function
        if re.match(
            r"^def register_.*_tools\(app, backend_manager: BackendManager, config: OCRConfig\):",
            line,
        ):
            in_wrapper = True
            continue

        # Detect docstring of register function or @app.tool()
        if in_wrapper and (re.match(r'^\s+"""', line) and "Register all" in line):
            continue

        if "@app.tool()" in line:
            continue

        # Unindent lines if inside wrapper
        if in_wrapper:
            if line.strip() == "":
                new_lines.append("\n")
            else:
                new_lines.append(line[4:])
        else:
            new_lines.append(line)

    with open(filepath, "w") as f:
        f.writelines(new_lines)


modules = [
    "src/ocr_mcp/tools/_analysis.py",
    "src/ocr_mcp/tools/_quality.py",
    "src/ocr_mcp/tools/_image.py",
    "src/ocr_mcp/tools/_conversion.py",
    "src/ocr_mcp/tools/_scanner.py",
    "src/ocr_mcp/tools/_workflow.py",
]

for mod in modules:
    print(f"Refactoring {mod}...")
    refactor_module(mod)
