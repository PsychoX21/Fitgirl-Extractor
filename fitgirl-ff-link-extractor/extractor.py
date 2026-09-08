import os
import sys
import re
import time
import tempfile
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
        
    # If the user directly pasted a fuckingfast.co link
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
            
            # Categorize link based on filename
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
    Creates browser driver configured for stealth Cloudflare Turnstile bypass.
    On Linux/Render: Uses Xvfb virtual frame buffer to render genuine desktop Chrome without bot flags.
    On Windows: Uses isolated temp profiles and off-screen window positioning.
    """
    b_name = browser_name.lower()
    is_windows = sys.platform.startswith('win')
    
    # Isolate profile directory to prevent collisions
    temp_profile = os.path.join(tempfile.gettempdir(), f"fg_uc_prof_{int(time.time()*1000)}")
    os.makedirs(temp_profile, exist_ok=True)
    
    if "firefox" in b_name:
        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options
        opts = Options()
        opts.binary_location = browser_path
        if headless and is_windows:
            opts.add_argument("-headless")
        opts.set_preference("dom.webdriver.enabled", False)
        return webdriver.Firefox(options=opts)
        
    elif "msedge" in b_name or "edge" in b_name:
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options
        opts = Options()
        opts.binary_location = browser_path
        opts.add_argument(f"--user-data-dir={temp_profile}")
        if headless:
            if is_windows:
                opts.add_argument("--window-position=-2500,-2500")
                opts.add_argument("--window-size=1280,800")
            else:
                opts.add_argument("--window-size=1920,1080")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        opts.add_argument("--disable-blink-features=AutomationControlled")
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
        
        if is_windows:
            if headless:
                # Offscreen window on Windows (undetectable by Cloudflare)
                opts.add_argument("--window-position=-2500,-2500")
                opts.add_argument("--window-size=1280,800")
        else:
            # On Linux (Docker/Render/VPS), Xvfb provides the virtual screen,
            # so we run standard GUI Chrome inside Xvfb (DISPLAY=:99)
            opts.add_argument("--window-size=1920,1080")
            # If no X11 display is available on Linux fallback to headless
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

def extract_direct_url_from_driver(driver, link: str, timeout_seconds: int = 35, heartbeat_callback=None):
    """
    Loads fuckingfast page, injects adblock & interceptors, clicks the download button
    as soon as Turnstile solves, and captures the direct download URL.
    """
    js_inject = """
    // 1. Block annoying popup ads
    window.open = function(u) {
        if (u && u.includes('dl.fuckingfast.co')) {
            document.body.setAttribute('data-direct-url', u);
        }
        return null;
    };
    
    // 2. Intercept XMLHttpRequest to catch hx-redirect or location headers
    if (!window.xhrIntercepted) {
        window.xhrIntercepted = true;
        var originalXHR = window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            var xhr = new originalXHR();
            xhr.addEventListener('readystatechange', function() {
                if (xhr.readyState === 4) {
                    var redirect = xhr.getResponseHeader('hx-redirect') || xhr.getResponseHeader('location');
                    if (redirect && redirect.includes('dl.fuckingfast.co')) {
                        document.body.setAttribute('data-direct-url', redirect);
                    }
                }
            });
            return xhr;
        };
    }

    // 3. Intercept fetch API as well
    if (!window.fetchIntercepted && window.fetch) {
        window.fetchIntercepted = true;
        var origFetch = window.fetch;
        window.fetch = async function(...args) {
            const res = await origFetch(...args);
            const redirect = res.headers.get('hx-redirect') || res.headers.get('location');
            if (redirect && redirect.includes('dl.fuckingfast.co')) {
                document.body.setAttribute('data-direct-url', redirect);
            }
            return res;
        };
    }
    """
    
    js_click = """
    let btn = document.querySelector('a[hx-post]');
    if (btn) {
        if (window.turnstileToken || window.dlCleared || (btn.style && btn.style.opacity !== '0.5')) {
            btn.click();
            return 'clicked';
        }
        return 'waiting_token';
    }
    return 'btn_not_found';
    """
    
    driver.get(link)
    try:
        driver.execute_script(js_inject)
    except Exception:
        pass
    
    start_time = time.time()
    while (time.time() - start_time) < timeout_seconds:
        time.sleep(0.8)
        
        if heartbeat_callback:
            heartbeat_callback()

        # Check intercepted URL or trigger click
        try:
            driver.execute_script(js_click)
            attr_val = driver.execute_script("return document.body.getAttribute('data-direct-url');")
            if attr_val and "dl.fuckingfast.co" in attr_val:
                return attr_val
        except Exception:
            pass

        # Fallback 1: Current browser navigation URL
        try:
            if "dl.fuckingfast.co" in driver.current_url:
                return driver.current_url
        except Exception:
            pass
            
        # Fallback 2: Search page source
        try:
            src = driver.page_source
            match = re.search(r'https?://dl\.fuckingfast\.co/[^\s\'"<>]+', src)
            if match:
                return match.group(0)
        except Exception:
            pass

    return None
