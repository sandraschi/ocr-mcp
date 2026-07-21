# Book Scanning with OCR-MCP

## A Brief History of Home Book Scanning

Before cloud OCR APIs and VLMs, building a digital library meant either destroying your books
or building elaborate rigs. The home scanning community (diybookscanner.org, circa 2008-2015)
pioneered two main approaches:

### The Cut-Away-Spine Method (destroy the book)

This is the fastest way to scan a book, but it hurts.

1. Buy a guillotine paper cutter (~$150)
2. Cut off the spine of the book
3. Feed the loose pages through a duplex document feeder scanner (Fujitsu ScanSnap or similar)
4. The scanner chews through 50+ pages per minute

**Pros:** Fast, clean OCR-ready scans, minimal post-processing.
**Cons:** The book is destroyed. You now have a stack of loose pages. Binding requires spiral
or comb binding if you want a physical copy back. Sandra's first few hundred ebooks were
done this way. Expensive in books.

### The V-Cradle Platenless Method (preserve the book)

The book rests in a V-shaped cradle. Pages hang down naturally on each side — no glass
pressed against the page. One or two overhead cameras capture the spread.

**Pros:** The book survives. No spine damage. Fast once set up (foot pedal trigger).
**Cons:** Page curve distortion needs software correction. Requires good lighting and a
copy stand or rig. Slower per-page than cutting.

## Modern Options (Still Available)

### Recommended: CZUR Overhead Scanners

CZUR is the only company still actively making home book scanners. They use an overhead
camera with edge lights — no glass pressing on the book. Built-in page curve flattening.

| Model | Price | Max Size | Notes |
|-------|-------|----------|-------|
| **CZUR ShineUltra** | ~$350 | A3 | Best all-rounder, foot pedal, WiFi |
| **CZUR ET24 Pro** | ~$250 | A3 | Good value, USB only |
| **CZUR Aura** | ~$200 | A4 | Portable, compact, good for paperbacks |

All three save to SD card or network folder. OCR-MCP can watch that folder and auto-process.

### DIY V-Cradle Rig

If you want the cheapest option and enjoy building things:

- **Camera:** Any 12MP+ used mirrorless or a Logitech Brio webcam (~$50-100 used)
- **Cradle:** Get a local metal shop to bend an aluminum V-trough (~$50)
- **Lighting:** Two LED desk lamps at 45 degrees (~$30)
- **Software:** CZUR's free software works with any camera. Or use ScanTailor + OpenCV.
- **Foot pedal:** USB foot pedal from Amazon (~$25)

Total: ~$150-250. Better scans than any flatbed for bound books.

### What NOT to buy

- **BE Book Scanner:** Long discontinued, no driver support, impossible to repair
- **Atiz BookDrive:** Same story — museum pieces
- **Flatbed scanners for books:** You have to press the book flat on the glass,
  which breaks spines on thick books and is painfully slow

## Integrating with OCR-MCP

### Auto-Scan Watcher

OCR-MCP has a built-in scanner watcher (since v0.2.0-beta) that can auto-detect
new documents:

**Preview-poll mode (default):** Takes a low-res preview scan every 3 seconds.
When the image changes (you placed a document), it triggers a full scan + OCR.
Works with any flatbed scanner. No hardware button needed.

**Button mode:** Listens for the scanner's physical scan button. When pressed,
triggers the OCR pipeline. Only works on scanners that expose button events via WIA.

**Enable it:**
- On the Dashboard, click the "Auto-Scan" button
- Or in Settings > Auto-Scan, toggle the switch
- Place a document on the scanner glass and close the lid
- OCR-MCP detects it, scans at 300 DPI, and runs Unlimited-OCR
- The result appears in the dashboard editor

### Folder Watcher (Future)

For CZUR scanners and other cameras that save to disk, a folder watcher will poll
a directory for new images and auto-submit them for OCR. On the roadmap.

## Workflow for Batch Scanning

```
1. Set up your camera/CZUR/scanner
2. Start OCR-MCP webapp
3. Enable Auto-Scan in Settings
4. Place book open on the scanner/cradle
5. Wait 3 seconds — auto-trigger detects the page
6. Page is scanned and OCR'd to text
7. Result appears in the dashboard
8. Turn the page, repeat
```

For CZUR users, a foot pedal triggers the camera capture. OCR-MCP can be configured
to watch the CZUR output folder and auto-process each new image (folder watcher feature
coming soon).

## See Also

- `src/ocr_mcp/services/scanner_watcher.py` — the auto-scan service
- Dashboard Auto-Scan toggle in the webapp
- Settings > Auto-Scan configuration
