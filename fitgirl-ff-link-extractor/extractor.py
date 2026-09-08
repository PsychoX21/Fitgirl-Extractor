import os
import sys
import re
import time
import tempfile
import gc
import requests
from bs4 import BeautifulSoup

def get_browser_path(selected_browser="Auto-Detect Browser"):
    """Find installed browser executables across Windows and Linux systems."""
    browser_paths = {
        "Google Chrome": [
            r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
            r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
            r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/var/lib/flatpak/exports/bin/com.google.Chrome"
        ],
        "Microsoft Edge": [
            r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
            r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
            r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe",
            "/usr/bin/microsoft-edge-stable",
            "/usr/bin/microsoft-edge"
        ],
        "Brave": [
            r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe",
            "/usr/bin/brave-browser",
            "/usr/bin/brave",
            "/var/lib/flatpak/exports/bin/com.brave.Browser"
        ],
        "Mozilla Firefox": [
            r"%ProgramFiles%\Mozilla Firefox\firefox.exe",
            r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe",
            r"%LocalAppData%\Mozilla Firefox\firefox.exe",
            "/usr/bin/firefox",
            "/var/lib/flatpak/exports/bin/org.mozilla.firefox"
        ]
    }
    
    if selected_browser != "Auto-Detect Browser":
        paths_to_check = browser_paths.get(selected_browser, [])
    else:
        paths_to_check = []
        for paths in browser_paths.values():
            paths_to_check.extend(paths)

    for path in paths_to_check:
        expanded = os.path.expandvars(path)
        if os.path.exists(expanded):
            return expanded
    return None

def fetch_links_from_url(url: str):
    """
    Fetch a FitGirl game page and extract fuckingfast.co links with categorized metadata.
    """
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")
        
    if "fuckingfast.co" in url and "fitgirl-repacks.site" not in url:
        name = url.split('#')[-1] if '#' in url else url.split('/')[-1]
        return {
            "title": name or "FuckingFast Link",
            "url": url,
            "links": [{
                "id": 0,
                "url": url,
                "name": name or "Part 1",
                "category": "main",
                "selected": True
            }]
        }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, 'html.parser')
    
    title_el = soup.find('h1', class_='entry-title') or soup.find('h1') or soup.find('title')
    page_title = title_el.get_text().strip() if title_el else "FitGirl Repack"

    ff_links = []
    seen = set()
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if 'fuckingfast.co' in href and href not in seen:
            seen.add(href)
            name = href.split('#')[-1] if '#' in href else href.split('/')[-1]
            
            name_lower = name.lower()
            if 'selective' in name_lower or 'optional' in name_lower or 'bonus' in name_lower or 'languages' in name_lower:
                category = "optional"
            elif 'setup' in name_lower or name_lower.endswith('.exe') or 'fg-0' in name_lower or 'fg-1' in name_lower:
                category = "setup"
            else:
                category = "main"

            ff_links.append({
                "id": len(ff_links),
                "url": href,
                "name": name,
                "category": category,
                "selected": True
            })

    return {
        "title": page_title,
        "url": url,
        "links": ff_links
    }

def create_selenium_driver(browser_name: str, browser_path: str, headless: bool = True):
    """
    Creates lightweight stealth browser driver.
    """
    b_name = browser_name.lower()
    is_windows = sys.platform.startswith('win')
    
    temp_profile = os.path.join(tempfile.gettempdir(), f"fg_uc_{int(time.time()*1000)}")
    os.makedirs(temp_profile, exist_ok=True)
    
    if "firefox" in b_name:
        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options
        opts = Options()
        opts.binary_location = browser_path
        if is_windows and headless:
            opts.add_argument("-headless")
        opts.set_preference("dom.webdriver.enabled", False)
        return webdriver.Firefox(options=opts)
        
    elif "msedge" in b_name or "edge" in b_name:
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options
        opts = Options()
        opts.binary_location = browser_path
        opts.add_argument(f"--user-data-dir={temp_profile}")
        if is_windows and headless:
            opts.add_argument("--window-position=-2500,-2500")
        opts.add_argument("--window-size=1280,800")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        return webdriver.Edge(options=opts)
        
    else: # Chrome / Brave / Chromium
        import undetected_chromedriver as uc
        opts = uc.ChromeOptions()
        
        opts.add_argument(f"--user-data-dir={temp_profile}")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-background-networking")
        opts.add_argument("--mute-audio")
        opts.add_argument("--window-size=1280,800")
        
        if is_windows:
            if headless:
                opts.add_argument("--window-position=-2500,-2500")
        else:
            # On Linux (Render / Docker), Xvfb provides the virtual screen (DISPLAY=:99)
            if not os.environ.get("DISPLAY"):
                opts.add_argument("--headless=new")
        
        try:
            return uc.Chrome(
                options=opts,
                use_subprocess=True,
                browser_executable_path=browser_path
            )
        except Exception as e:
            err_str = str(e)
            match = re.search(r"Current browser version is (\d+)", err_str)
            if match:
                version = int(match.group(1))
                return uc.Chrome(
                    options=opts,
                    use_subprocess=True,
                    browser_executable_path=browser_path,
                    version_main=version
                )
            raise e

def extract_direct_url_from_driver(driver, link: str, timeout_seconds: int = 30, heartbeat_callback=None):
    """
    Loads fuckingfast page, syncs Turnstile token from both window and hidden inputs,
    attaches htmx listeners, clicks download, and captures the direct download URL.
    """
    driver.get(link)
    
    js_setup = """
    window.directDlUrl = null;
    
    window.open = function(u) {
        if (u && u.includes('dl.fuckingfast.co')) {
            window.directDlUrl = u;
            document.body.setAttribute('data-direct-url', u);
        }
        return null;
    };

    document.body.addEventListener('htmx:afterRequest', function(e) {
        if (e.detail && e.detail.xhr) {
            var redir = e.detail.xhr.getResponseHeader('hx-redirect') || e.detail.xhr.getResponseHeader('location');
            if (redir && redir.includes('dl.fuckingfast.co')) {
                window.directDlUrl = redir;
                document.body.setAttribute('data-direct-url', redir);
            }
        }
    });

    if (!window.xhrWrapped) {
        window.xhrWrapped = true;
        var origXHR = window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            var xhr = new origXHR();
            xhr.addEventListener('readystatechange', function() {
                if (xhr.readyState === 4) {
                    var redir = xhr.getResponseHeader('hx-redirect') || xhr.getResponseHeader('location');
                    if (redir && redir.includes('dl.fuckingfast.co')) {
                        window.directDlUrl = redir;
                        document.body.setAttribute('data-direct-url', redir);
                    }
                }
            });
            return xhr;
        };
    }
    """
    try:
        driver.execute_script(js_setup)
    except Exception:
        pass

    start_time = time.time()
    while (time.time() - start_time) < timeout_seconds:
        time.sleep(0.7)
        
        if heartbeat_callback:
            heartbeat_callback()

        # 1. Sync Turnstile input value to window.turnstileToken if available
        try:
            driver.execute_script("""
                let input = document.querySelector('#cf-turnstile input[name="cf-turnstile-response"]') || document.querySelector('input[name="cf-turnstile-response"]');
                if (input && input.value) {
                    window.turnstileToken = input.value;
                }
            """)
        except Exception:
            pass

        # 2. Check if URL was captured
        try:
            captured = driver.execute_script("return window.directDlUrl || document.body.getAttribute('data-direct-url');")
            if captured and "dl.fuckingfast.co" in captured:
                gc.collect()
                return captured
        except Exception:
            pass

        # 3. If Turnstile widget is present, click it or click download button
        try:
            driver.execute_script("""
                let turnstileEl = document.querySelector('#cf-turnstile iframe, #cf-turnstile, div.cf-turnstile');
                if (turnstileEl && !window.turnstileToken) {
                    try { turnstileEl.click(); } catch(e) {}
                }
                
                let b = document.querySelector('a[hx-post]');
                if (b && (window.turnstileToken || window.dlCleared || (b.style && b.style.opacity !== '0.5'))) {
                    b.click();
                }
            """)
        except Exception:
            pass

        # Fallback 1: Current navigation URL
        try:
            if "dl.fuckingfast.co" in driver.current_url:
                gc.collect()
                return driver.current_url
        except Exception:
            pass
            
        # Fallback 2: Page source regex
        try:
            src = driver.page_source
            match = re.search(r'https?://dl\.fuckingfast\.co/[^\s\'"<>]+', src)
            if match:
                gc.collect()
                return match.group(0)
        except Exception:
            pass

    gc.collect()
    return None
