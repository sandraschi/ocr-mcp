import os
import re


def fix_content(filepath):
    print(f"Fixing {filepath}...")
    with open(filepath, "r") as f:
        lines = f.readlines()

    new_lines = []

    # First pass: Fix corrupted keywords
    for line in lines:
        # Fix repeated prefixes
        line = re.sub(r"(asyn)+async def", "async def", line)
        line = re.sub(r"(asy)+async def", "async def", line)
        line = re.sub(r"(Op)+Operation", "Operation", line)
        line = re.sub(r"(Or)+Original", "Original", line)
        line = re.sub(r"(iginal)+Original", "Original", line)
        line = re.sub(r"^c def", "async def", line)

        new_lines.append(line)

    # Second pass: Fix indentation
    final_lines = []
    in_function = False

    for line in new_lines:
        stripped = line.lstrip()

        # Check if this is the start of a function
        if stripped.startswith("async def ") or stripped.startswith("def "):
            in_function = True
            final_lines.append(line)
            continue

        # If we are in a function and the line has no indentation and is not empty
        if (
            in_function
            and stripped
            and not line.startswith("    ")
            and not line.startswith("\t")
        ):
            # If it's another top level element (like docstring at top level or something)
            # or if it's just content that needs indentation
            final_lines.append("    " + line)
        else:
            final_lines.append(line)

    with open(filepath, "w") as f:
        f.writelines(final_lines)


tools_dir = "src/ocr_mcp/tools"
for filename in os.listdir(tools_dir):
    if filename.endswith(".py"):
        fix_content(os.path.join(tools_dir, filename))
print("All files fixed.")
