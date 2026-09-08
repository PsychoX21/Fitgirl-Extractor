import os
import json
import asyncio
import uuid
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

import extractor

app = FastAPI(title="FitGirl Direct Link Extractor", version="2.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Active extraction sessions
active_sessions = {}

class FetchRequest(BaseModel):
    url: str

class ExtractionItem(BaseModel):
    id: int
    url: str
    name: str
    category: Optional[str] = "main"

class StartExtractionRequest(BaseModel):
    links: List[ExtractionItem]
    browser: str = "Auto-Detect Browser"
    headless: bool = True

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/browsers")
async def get_browsers():
    browser_options = [
        "Auto-Detect Browser",
        "Google Chrome",
        "Microsoft Edge",
        "Brave",
        "Mozilla Firefox"
    ]
    detected = {}
    for b in browser_options:
        path = extractor.get_browser_path(b)
        detected[b] = {
            "available": bool(path),
            "path": path or ""
        }
    return detected

@app.post("/api/fetch")
async def fetch_fitgirl_page(req: FetchRequest):
    try:
        data = await asyncio.to_thread(extractor.fetch_links_from_url, req.url)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/extract/start")
async def start_extraction(req: StartExtractionRequest):
    if not req.links:
        raise HTTPException(status_code=400, detail="No links provided")
    
    session_id = str(uuid.uuid4())
    cancel_flag = {"cancelled": False}
    active_sessions[session_id] = {
        "links": req.links,
        "browser": req.browser,
        "headless": req.headless,
        "cancel_flag": cancel_flag,
        "queue": asyncio.Queue()
    }
    
    asyncio.create_task(run_extraction_task(session_id))
    return {"success": True, "session_id": session_id}

@app.post("/api/extract/cancel/{session_id}")
async def cancel_extraction(session_id: str):
    session = active_sessions.get(session_id)
    if session:
        session["cancel_flag"]["cancelled"] = True
        return {"success": True, "message": "Cancellation requested"}
    return {"success": False, "message": "Session not found"}

async def run_extraction_task(session_id: str):
    session = active_sessions.get(session_id)
    if not session:
        return

    queue: asyncio.Queue = session["queue"]
    links: List[ExtractionItem] = session["links"]
    browser_choice = session["browser"]
    headless = session["headless"]
    cancel_flag = session["cancel_flag"]

    def worker():
        browser_executable = extractor.get_browser_path(browser_choice)
        if not browser_executable:
            asyncio.run_coroutine_threadsafe(
                queue.put({"type": "error", "message": f"Browser '{browser_choice}' not found on system."}),
                loop
            )
            return

        browser_name = os.path.basename(browser_executable).replace('.exe', '')
        
        asyncio.run_coroutine_threadsafe(
            queue.put({
                "type": "log",
                "message": f"Initializing stealth {browser_name} (Headless: {headless})..."
            }),
            loop
        )

        driver = None
        try:
            driver = extractor.create_selenium_driver(browser_name, browser_executable, headless=headless)
            
            # Disable downloads globally
            if "firefox" not in browser_name.lower():
                try:
                    driver.execute_cdp_cmd(
                        "Browser.setDownloadBehavior", {
                            "behavior": "deny",
                            "downloadPath": os.path.abspath(os.sep)
                        }
                    )
                except Exception:
                    pass

            total = len(links)
            successful = 0
            failed = 0

            for i, item in enumerate(links, 1):
                if cancel_flag.get("cancelled"):
                    asyncio.run_coroutine_threadsafe(
                        queue.put({"type": "log", "message": "Extraction stopped by user."}),
                        loop
                    )
                    break

                asyncio.run_coroutine_threadsafe(
                    queue.put({
                        "type": "progress",
                        "current": i,
                        "total": total,
                        "percent": int(((i - 1) / total) * 100),
                        "current_item": item.name
                    }),
                    loop
                )

                asyncio.run_coroutine_threadsafe(
                    queue.put({
                        "type": "log",
                        "message": f"[{i}/{total}] Resolving direct link: {item.name}"
                    }),
                    loop
                )

                def heartbeat():
                    asyncio.run_coroutine_threadsafe(
                        queue.put({"type": "ping"}),
                        loop
                    )

                direct_url = None
                error_msg = None
                try:
                    direct_url = extractor.extract_direct_url_from_driver(
                        driver, item.url, timeout_seconds=20, heartbeat_callback=heartbeat
                    )
                except Exception as e:
                    error_msg = str(e)

                if direct_url:
                    successful += 1
                    asyncio.run_coroutine_threadsafe(
                        queue.put({
                            "type": "item_result",
                            "id": item.id,
                            "original_url": item.url,
                            "name": item.name,
                            "direct_url": direct_url,
                            "success": True
                        }),
                        loop
                    )
                    asyncio.run_coroutine_threadsafe(
                        queue.put({
                            "type": "log",
                            "message": f"✓ [SUCCESS] {item.name} -> {direct_url}"
                        }),
                        loop
                    )
                else:
                    failed += 1
                    asyncio.run_coroutine_threadsafe(
                        queue.put({
                            "type": "item_result",
                            "id": item.id,
                            "original_url": item.url,
                            "name": item.name,
                            "direct_url": None,
                            "success": False,
                            "error": error_msg or "Timed out resolving direct URL"
                        }),
                        loop
                    )
                    asyncio.run_coroutine_threadsafe(
                        queue.put({
                            "type": "log",
                            "message": f"✗ [FAILED] {item.name}: {error_msg or 'Timed out'}"
                        }),
                        loop
                    )

            asyncio.run_coroutine_threadsafe(
                queue.put({
                    "type": "progress",
                    "current": total,
                    "total": total,
                    "percent": 100,
                    "current_item": "Done"
                }),
                loop
            )

            asyncio.run_coroutine_threadsafe(
                queue.put({
                    "type": "done",
                    "total": total,
                    "successful": successful,
                    "failed": failed
                }),
                loop
            )

        except Exception as e:
            asyncio.run_coroutine_threadsafe(
                queue.put({"type": "error", "message": f"Critical Error: {str(e)}"}),
                loop
            )
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    loop = asyncio.get_running_loop()
    await asyncio.to_thread(worker)

@app.get("/api/extract/stream/{session_id}")
async def stream_extraction(session_id: str):
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    queue: asyncio.Queue = session["queue"]

    async def event_generator():
        try:
            while True:
                # 15s timeout with automatic heartbeat ping
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield {
                        "event": "message",
                        "data": json.dumps({"type": "ping"})
                    }
                    continue

                yield {
                    "event": "message",
                    "data": json.dumps(data)
                }
                if data.get("type") in ("done", "error"):
                    if session_id in active_sessions:
                        del active_sessions[session_id]
                    break
        except asyncio.CancelledError:
            pass

    return EventSourceResponse(event_generator(), ping=10)

if __name__ == "__main__":
    import uvicorn
    print("=======================================================")
    print("  🚀 FitGirl Direct Link Extractor Web Server")
    print("  🌐 Open in your browser: http://127.0.0.1:8000")
    print("=======================================================")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
