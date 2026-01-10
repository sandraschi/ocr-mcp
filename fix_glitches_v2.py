import os
import re


def fix_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Fix glitches (regex for asy*async)
    content = re.sub(r"asyn?async\s*def", "async def", content)
    content = re.sub(r"asy\s*async\s*def", "async def", content)
    content = content.replace("c def", "async def")

    # 2. Replace print statements with logging
    # Match print(...) at start of line or with indentation
    content = re.sub(r"(?m)^(\s*)print\((.*?)\)", r"\1logger.info(\2)", content)

    # 3. Fix bare excepts and make them more informative
    # Replace 'except:' or 'except Exception:' with 'except Exception as e:'
    # and add a logger.error(f"Error: {e}") if it's one-liner pass or dummy
    content = re.sub(
        r"except\s*:|except\s+Exception\s*:", "except Exception as e:", content
    )

    # Identify the indentation of the line after 'except Exception as e:'
    # and add a logger.error if missing.
    # This is tricky with regex, so we'll do a simpler replacement for now
    # to at least avoid the "bare" part.

    # 4. Fix specific function names
    content = content.replace("def register_ocr_tools", "def register_sota_tools")

    # 5. Add docstrings and logging import if missing
    if "import logging" not in content and "from logging" not in content:
        # Prepend to content but after potential encoding or frontmatter
        content = "import logging\nlogger = logging.getLogger(__name__)\n" + content
    elif "logger =" not in content and "logger=" not in content:
        # Avoid double import but ensure logger is defined
        content = content.replace(
            "import logging",
            "import logging\nlogger = logging.getLogger(__name__)\n",
            1,
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


# Process src and scripts
dirs_to_fix = ["src", "scripts"]
for dir_name in dirs_to_fix:
    full_path = os.path.join(os.getcwd(), dir_name)
    if not os.path.exists(full_path):
        continue

    for root, dirs, files in os.walk(full_path):
        for filename in files:
            if filename.endswith(".py") and filename != "__init__.py":
                filepath = os.path.join(root, filename)
                print(f"Fixing {filepath}...")
                fix_file(filepath)
