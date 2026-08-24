"""Pack OCR-MCP server into a standardized .mcpb bundle archive."""

import pathlib
import zipfile


def pack_mcpb():
    dist_dir = pathlib.Path("dist")
    dist_dir.mkdir(exist_ok=True)
    mcpb_path = dist_dir / "ocr-mcp.mcpb"

    with zipfile.ZipFile(mcpb_path, "w", zipfile.ZIP_DEFLATED) as z:
        for fname in ["manifest.json", "mcpb.json", "README.md", "LICENSE"]:
            if pathlib.Path(fname).exists():
                z.write(fname)

        src_dir = pathlib.Path("src")
        if src_dir.exists():
            for p in src_dir.rglob("*"):
                if p.is_file() and "__pycache__" not in p.parts:
                    z.write(p)

        assets_dir = pathlib.Path("assets")
        if assets_dir.exists():
            for p in assets_dir.rglob("*"):
                if p.is_file():
                    z.write(p)

    size = mcpb_path.stat().st_size
    print(f"[OK] MCPB bundle created: {mcpb_path} ({size} bytes / {size / 1024:.1f} KB)")


if __name__ == "__main__":
    pack_mcpb()
