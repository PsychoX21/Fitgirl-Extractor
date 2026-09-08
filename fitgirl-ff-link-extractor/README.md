# ⚡ FitGirl Direct Link Extractor (Web Edition)

A high-speed, automated web application and stealth scraper built with **FastAPI**, **Selenium**, and **Server-Sent Events (SSE)**. It parses FitGirl Repack pages, bypasses Cloudflare Turnstile & countdown timers on hoster links (`fuckingfast.co`), and extracts direct high-speed download URLs (`dl.fuckingfast.co`) in real-time.

---

## ✨ Features

- **⚡ Fast Parsing:** Instantly pulls game titles, setup binaries, optional voicepacks, and all multipart archive links.
- **🌐 Modern Dark/Neon Web UI:** Glassmorphism dashboard with live console output, animated progress bars, and toast notifications.
- **🚀 Real-Time SSE Streaming:** Direct download links stream into your browser as each part resolves.
- **🛡️ Cloudflare & Adblock Stealth:** Injects adblock/XHR listeners and runs undetected browser instances to eliminate popups and timer waits.
- **⚙️ Headless or Visible Mode:** Run silently in the background (default) or toggle the browser window for debugging.
- **🔍 Dynamic Part Filtering & Selection:** Select All / Deselect All or filter parts in real-time by typing keywords (e.g., `part01`, `setup`, `optional`).
- **📦 JDownloader / IDM / Aria2 Ready:** 1-Click "Copy All Links" or export directly to a `.txt` file.
- **🐳 Cloud & Docker Ready:** Fully containerized with Google Chrome for 1-click cloud deployment.

---

## 🚀 Running Locally

### Option 1: One-Click Launcher (Windows)
Double-click [`run_web.bat`](file:///c:/Users/khand/Downloads/Fitgirl%20Extractor/fitgirl-ff-link-extractor/run_web.bat). It will start the server and open your default browser.

### Option 2: Command Line (Windows / Linux / macOS)
1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Web Server:**
   ```bash
   python app.py
   ```

3. **Open the Web UI:**
   Navigate to [**http://127.0.0.1:8000**](http://127.0.0.1:8000) in any browser.

---

## ☁️ Cloud & Remote Deployment (Zero Local Installation)

You can host this application in the cloud and use it from any phone, laptop, or browser without installing anything on your computer.

### Deploy with Docker
```bash
# Build the Docker image
docker build -t fitgirl-extractor .

# Run container on port 8000
docker run -d -p 8000:8000 --name fitgirl-extractor fitgirl-extractor
```

### Free & Low-Cost Cloud Platforms

| Platform | Deployment Instructions |
| :--- | :--- |
| **[Render](https://render.com)** | 1. Create a **New Web Service** pointing to your Git repository.<br>2. Select **Docker** environment.<br>3. Deploy! |
| **[Railway](https://railway.app)** | 1. Create a **New Project** and connect your repository.<br>2. Railway automatically detects the [`Dockerfile`](file:///c:/Users/khand/Downloads/Fitgirl%20Extractor/fitgirl-ff-link-extractor/Dockerfile) and provisions the app. |
| **[Hugging Face Spaces](https://huggingface.co/spaces)** | 1. Create a Space with the **Docker SDK**.<br>2. Push the files and access your free persistent public URL. |
| **Linux VPS (Ubuntu / Debian)** | Run `docker-compose up -d` or start via systemd/PM2. |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Web dashboard interface |
| `GET` | `/api/browsers` | Detects installed browser binaries on host |
| `POST` | `/api/fetch` | Parses a FitGirl game URL and returns available parts |
| `POST` | `/api/extract/start` | Starts background link extraction session |
| `GET` | `/api/extract/stream/{session_id}` | Server-Sent Events (SSE) stream for live progress & links |
| `POST` | `/api/extract/cancel/{session_id}` | Cancels an active extraction job |

---

## 📁 Project Structure

```
fitgirl-ff-link-extractor/
├── app.py                 # FastAPI backend & SSE streaming endpoints
├── extractor.py           # Stealth browser automation engine
├── requirements.txt       # Python dependencies
├── Dockerfile             # Production Linux/Chrome container for cloud hosting
├── run_web.bat            # Windows 1-click launcher
├── templates/
│   └── index.html         # Responsive web UI dashboard
└── static/
    ├── css/
    │   └── style.css      # Dark/emerald cyberpunk styling
    └── js/
        └── app.js         # Reactive UI, SSE handler & export utilities
```
