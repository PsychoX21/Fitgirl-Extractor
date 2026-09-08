# FitGirl Direct Link Extractor (Web & GUI Edition)

A modern, high-speed automated extraction engine built in Python and FastAPI to retrieve, filter, and extract direct download links (`dl.fuckingfast.co`) from FitGirl Repack pages.

---

## 🌐 Web Edition Features (New)
- **⚡ Modern Responsive Web UI**: Sleek dark/neon aesthetic with live progress feedback, real-time logging, and interactive part filtering.
- **🚀 Server-Sent Events (SSE)**: Streams extraction status, progress percentages, and direct download links in real-time as each link resolves.
- **🛡️ Cloudflare & Adblock Stealth**: Automatically handles popups, cookies, timers, and cloudflare verification using undetected automation.
- **⚙️ Headless or Visible Mode**: Toggle headless mode on/off in real-time or select between Chrome, Edge, Brave, and Firefox.
- **📦 JDownloader / IDM / Aria2 Export**: One-click "Copy All Links" or "Export .TXT" file.
- **🔍 Instant Search & Multi-Select**: Filter parts dynamically by keyword (e.g., `setup`, `optional`, `part01`).

---

## 🚀 How to Run the Web Application

### Option 1: One-Click Launcher (Windows)
Double-click [`run_web.bat`](file:///c:/Users/khand/Downloads/Fitgirl%20Extractor/fitgirl-ff-link-extractor/run_web.bat). It will automatically start the server and open your default browser.

### Option 2: Command Line
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the FastAPI server:
   ```bash
   python app.py
   ```
3. Open your browser at:
   ```
   http://127.0.0.1:8000
   ```

---

## 🖥️ Desktop GUI Edition
If you prefer the original Tkinter desktop GUI app, you can still run:
```bash
python ff_grabber.py
```
