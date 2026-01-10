import os
import re


def fix_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Fix glitches (regex for asy*async)
    content = re.sub(r"asyn?async def", "async def", content)
    content = re.sub(r"asy async def", "async def", content)
    content = content.replace("c def", "async def")

    # 2. Replace print statements with logging
    # Match print(...) at start of line or with indentation
    content = re.sub(r"(?m)^(\s*)print\((.*?)\)", r"\1logger.info(\2)", content)

    # 3. Fix bare excepts
    content = content.replace("except:", "except Exception:")

    # 4. Add docstrings and logging import if missing
    if "import logging" not in content and "from logging" not in content:
        content = "import logging\nlogger = logging.getLogger(__name__)\n" + content

    if not content.strip().startswith('"""'):
        filename = os.path.basename(filepath)
        content = (
            f'"""\nOCR-MCP: {filename.replace(".py", "").replace("_", " ").title()}\n"""\n\n'
            + content
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


base_dir = "src/ocr_mcp"
for root, dirs, files in os.walk(base_dir):
    for filename in files:
        if filename.endswith(".py") and filename != "__init__.py":
            filepath = os.path.join(root, filename)
            print(f"Fixing {filepath}...")
            fix_file(filepath)
