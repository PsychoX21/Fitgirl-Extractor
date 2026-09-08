import os
import sys
import re
import time
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
    Fetch a FitGirl game page (or handles raw direct link list) and extract fuckingfast.co links.
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
            "links": [{"id": 0, "url": url, "name": name or "Part 1", "selected": True}]
        }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
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
            ff_links.append({
                "id": len(ff_links),
                "url": href,
                "name": name,
                "selected": True
            })

    return {
        "title": page_title,
        "url": url,
        "links": ff_links
    }

def create_selenium_driver(browser_name: str, browser_path: str, headless: bool = True):
    """Creates driver configured for stealth and popup blocking."""
    b_name = browser_name.lower()
    
    if "firefox" in b_name:
        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options
        opts = Options()
        opts.binary_location = browser_path
        if headless:
            opts.add_argument("-headless")
        opts.set_preference("dom.webdriver.enabled", False)
        return webdriver.Firefox(options=opts)
        
    elif "msedge" in b_name or "edge" in b_name:
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options
        opts = Options()
        opts.binary_location = browser_path
        if headless:
            opts.add_argument("--headless=new")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1280,800")
        return webdriver.Edge(options=opts)
        
    else: # Chrome / Brave / Chromium
        import undetected_chromedriver as uc
        opts = uc.ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1280,800")
        
        try:
            return uc.Chrome(
                options=opts,
                use_subprocess=True,
                browser_executable_path=browser_path,
                headless=headless
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
                    version_main=version,
                    headless=headless
                )
            raise e

def extract_direct_url_from_driver(driver, link: str, timeout_seconds: int = 30):
    """
    Loads page, injects adblock/XHR listener, clicks download button, and extracts direct link.
    """
    js_inject = """
    // 1. Block popup windows
    window.open = function() { return null; };
    
    // 2. Intercept XMLHttpRequest to catch direct redirect URL
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
    """
    
    js_click = """
    let btn = document.querySelector('a[hx-post]');
    if (btn && btn.style.opacity !== '0.5') {
        btn.click();
    }
    return document.body.getAttribute('data-direct-url');
    """
    
    driver.get(link)
    driver.execute_script(js_inject)
    
    start_time = time.time()
    while (time.time() - start_time) < timeout_seconds:
        time.sleep(1)
        
        # Check intercepted URL or trigger click
        result = driver.execute_script(js_click)
        if result and "dl.fuckingfast.co" in result:
            return result
            
        # Fallback 1: Current navigation URL
        if "dl.fuckingfast.co" in driver.current_url:
            return driver.current_url
            
        # Fallback 2: Regex in page source
        src = driver.page_source
        match = re.search(r'window\.open\("([^"]+dl\.fuckingfast\.co[^"]+)"\)', src)
        if match:
            return match.group(1)
            
        match_general = re.search(r'https?://dl\.fuckingfast\.co/[^\s\'"<>]+', src)
        if match_general:
            return match_general.group(0)

    return None
