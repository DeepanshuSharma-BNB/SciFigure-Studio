<div align="center">

<img src="logo.png" width="96" alt="SciFigure Studio logo">

# SciFigure Studio

**PDF cropper + scientific figure panel composer — in a single HTML file.**

No installation. No dependencies. Runs entirely in your browser — your files never leave your computer.

</div>

---

## What's in this repo

| File | Purpose |
|---|---|
| `SciFigure Studio.exe` | Launcher with logo — double-click to start (Windows) |
| `SciFigureStudio.html` | The complete app (single file; open directly in Chrome/Edge) |
| `logo.png` / `app.ico` | Logo, and icon file for making your own shortcuts |

## Getting started

1. Download `SciFigure Studio.exe` and `SciFigureStudio.html` (or clone the repo) and keep them **in the same folder**.
2. Double-click the `.exe` — or simply open `SciFigureStudio.html` in Chrome or Edge.

> **Notes**
>
> - First run: Windows SmartScreen may warn (unsigned app) — click **More info → Run anyway**.
> - Chrome or Edge is recommended: they provide the native Save-As dialog (choose file name **and** location).
> - Internet is needed the first time, for the PDF engine (pdf.js) and the TIFF decoder (loaded from CDN).

## Features

### Tab 1 — PDF → Image

- Open or drag-and-drop a PDF; page navigation and zoom.
- Drag to select a region — move it, or resize with corner handles.
- **Save Selection** / **Save Full Page** as PNG at 150–1200 DPI, with real DPI metadata (`pHYs` chunk) embedded — Photoshop, Word and journals read it correctly.
- The page is re-rendered at full target DPI (never upscaled from the screen preview), so crops stay sharp.
- **Send to Panel N → Composer** pushes a crop straight into a figure panel.

### Tab 2 — Figure Composer

- 1–10 panels with automatic grid layout; adjustable padding, canvas size and background color.
- Load images (PNG, JPG, BMP, WebP, GIF, **TIFF**) — selecting multiple files fills panels in order.
- Mouse: **drag** = move image, **wheel** = zoom, **double-click** a panel = load image.
- **ROI mode**: drag a green box, then *Apply ROI crop* (*Undo crop* restores the original).
- Per-panel adjustments: brightness, contrast, saturation, sharpness.
- Scale bars: length, thickness, text, font size, color, position — with copy-to-all-panels.
- Automatic panel labels (`a b c` / `A B C` / `1 2 3`), adjustable size and color.
- Export the figure as PNG with DPI tag, or copy it straight to the clipboard.

## Privacy

Everything runs client-side in your browser. PDFs and images are processed locally and are never uploaded anywhere.

---
## License
This project is licensed under MIT — free to use, modify and share license. This license allows you to use, modify, and distribute the software for non-commercial purposes only. Commercial use is prohibited without explicit permission from the copyright holder. Additionally, you may not patent or claim intellectual property rights over the software or any derivative works.

© Sharma, Deepanshu (2026), Germany.
---
*SciFigure Studio v1.0*
