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

- **Camera:** An **iPhone (or any modern smartphone)** is genuinely good enough now.
  A 12MP+ iPhone from the last few years (XR or newer) has higher effective resolution
  than many DSLRs from the 2000s. The key advantage: you already own it, and there are
  free apps with remote shutter + timer. Mount it on a cheap copy stand or tripod.
  The iPhone's built-in HDR and auto-focus handle lighting better than most webcams.
  For the truly dedicated, a used Google Pixel (which has best-in-class document
  capture algorithms) is ~$50-100 used.
- **Cradle:** Get a local metal shop to bend an aluminum V-trough (~$50).
  Or build one from plywood in an afternoon — many free plans online from the
  DIY book scanning community.
- **Lighting:** Two LED desk lamps at 45 degrees (~$30). The iPhone compensates for
  uneven lighting better than older cameras, but even light still helps.
- **Software:** The iPhone's built-in Notes app can scan documents (auto-crop, deskew)
  and export to PDF. For book scanning, **Microsoft Lens** (free) or **Adobe Scan**
  (free) handle page curve flattening better. For the full DIY workflow:
  ScanTailor + OpenCV on the desktop.
- **Foot pedal:** USB foot pedal from Amazon (~$25) for hands-free capture.
  Or use the iPhone's voice shutter: "Hey Siri, take a picture."
- **Remote camera app:** Many free apps let you trigger the iPhone camera from a
  browser on your laptop — no foot pedal needed.

**Total with iPhone you already own: ~$105 (cradle + lights + pedal).**
Total with used Pixel: ~$155-205.

Better scans than any flatbed for bound books, and the iPhone's 4K video mode
lets you record a page-flip session and extract frames — 30 pages/minute with
no manual shutter pressing. There are iOS apps (Scanner Pro, Adobe Scan) that
do this automatically.

### What NOT to buy

- **BE Book Scanner:** Long discontinued, no driver support, impossible to repair
- **Atiz BookDrive:** Same story — museum pieces
- **Flatbed scanners for books:** You have to press the book flat on the glass,
  which breaks spines on thick books and is painfully slow

## Video Frame Extraction (iPhone Book Scanner)

The simplest book scanner you can build today:

1. Mount your iPhone on a cheap copy stand above a V-cradle
2. Start 4K video recording in good light
3. Flip pages naturally — one hand, steady rhythm
4. Stop recording after 200 pages (~6 minutes)
5. Run a script that extracts frames where the page is stable (no motion blur)
6. Feed the extracted frames to OCR-MCP's batch pipeline

**Frame extraction logic:**

```python
# For each frame, check Laplacian variance (focus measure)
# When variance spikes above threshold after a dip, a new page
# has settled into place — grab that frame
variance = cv2.Laplacian(frame, cv2.CV_64F).var()
if variance > sharp_threshold and was_blurry:
    save_frame(frame, f"page_{page_num:03d}.png")
    page_num += 1
```

No shutter button, no foot pedal, no scanner. Just flip pages and OCR-MCP handles
the rest. The entire 200-page book goes from video to EPUB in one batch.

iPhone apps that already do this: **Scanner Pro**, **Adobe Scan**, **Microsoft Lens**.
But none of them feed into OCR-MCP's chapter detector + EPUB pipeline. That's
where the custom pipeline wins.

## Camera-Lid Integration (with devices-mcp)

A clever escalation of the auto-scan idea: instead of polling the scanner's preview,
use a **cheap USB webcam** pointed at the scanner to watch for physical interaction.

**The flow:**

```
Camera watches scanner ──► detects lid open ──► waits for lid close
    │                              │                      │
    │  OpenCV motion detect        │  paper placed        │  trigger scan + OCR
    │  + object presence           │  (camera sees it)    │
    ▼                              ▼                      ▼
  "lid opened"                  "paper on glass"       "lid closed — scan!"
```

**How it works with devices-mcp:**

1. A USB webcam (~$20-40) is aimed at the flatbed scanner from the side
2. devices-mcp exposes the camera feed to OCR-MCP
3. OCR-MCP runs a simple OpenCV loop:
   - **Lid open detected:** When the camera sees the scanner lid rise (motion in the upper region of the frame)
   - **Paper detected:** When a new rectangular object appears on the glass (contour detection)
   - **Lid closed:** When the lid returns to its original position
   - **Trigger:** Full 300 DPI scan + Unlimited-OCR
4. No scanning software, no WIA events, no preview-poll — just a camera watching the physical world

**Why this is better than preview-poll:**

| Method | Pros | Cons |
|--------|------|------|
| Preview-poll | No extra hardware | Wastes scanner cycles, slow (3s interval) |
| WIA button events | Clean | Scanner-dependent, unreliable |
| **Camera visual** | Instant, zero scanner wear, works with any scanner | Needs a webcam, OpenCV setup |

**Estimated cost:** $20-40 for a USB webcam (Logitech C270 or similar).
Mount it on a small arm or just tape it to a nearby shelf pointing at the scanner.
No modification to the scanner needed.

**Roadmap integration:**

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ devices-mcp     │────►│ OCR-MCP          │────►│ Scanner + Pipeline│
│ USB camera feed │     │ visual watcher   │     │ auto scan + OCR   │
│ OpenCV detect   │     │ lid+paper events │     │ chapter detect    │
└─────────────────┘     └──────────────────┘     └──► EPUB out       │
                                                     └──────────────────┘
```

This idea is not implemented yet, but the building blocks all exist:
- `devices-mcp` exposes camera feeds as MCP resources
- `scanner_watcher.py` has the trigger framework (just needs a new detection mode)
- The book pipeline handles everything after the scan

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
