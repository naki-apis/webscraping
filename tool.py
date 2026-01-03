import time
import random
import requests
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

class WebScraper:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.absolute()
        self.selenium_dir = self.base_dir / "selenium"
        self.session = requests.Session()
        self.driver = None
    
    def _setup_selenium_paths(self):
        chrome_path = self.selenium_dir / "chrome-linux64" / "chrome"
        if not chrome_path.exists():
            chrome_path = self.selenium_dir / "chrome" / "chrome"
            if not chrome_path.exists():
                chrome_path = self.selenium_dir / "chrome.exe"
        
        chromedriver_path = self.selenium_dir / "chromedriver-linux64" / "chromedriver"
        if not chromedriver_path.exists():
            chromedriver_path = self.selenium_dir / "chromedriver" / "chromedriver"
            if not chromedriver_path.exists():
                chromedriver_path = self.selenium_dir / "chromedriver.exe"
        
        return chrome_path, chromedriver_path
    
    def _create_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        chrome_path, chromedriver_path = self._setup_selenium_paths()
        
        if chrome_path.exists():
            chrome_options.binary_location = str(chrome_path)
        
        try:
            if chromedriver_path.exists():
                service = Service(executable_path=str(chromedriver_path))
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
            })
            
            return True
        except:
            return False
    
    def _wait_for_cloudflare(self, timeout=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            page_source = self.driver.page_source
            if any(text in page_source for text in ["Just a moment", "Verifying you are human", "cloudflare", "Challenge"]):
                time.sleep(random.uniform(3, 6))
                self.driver.execute_script("window.scrollBy(0, 200);")
                time.sleep(random.uniform(1, 3))
            else:
                return True
        return False
    
    def scrape_with_selenium(self, url, wait_for_element=None, timeout=20):
        if not self._create_driver():
            return None
        
        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))
            
            self._wait_for_cloudflare()
            
            if wait_for_element:
                by, selector = wait_for_element
                try:
                    WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((by, selector))
                    )
                except TimeoutException:
                    pass
            
            time.sleep(random.uniform(1, 3))
            
            return self.driver.page_source
            
        except:
            return None
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                except:
                    pass
    
    def scrape_with_requests(self, url, headers=None, timeout=20):
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        if headers:
            default_headers.update(headers)
        
        try:
            response = self.session.get(url, headers=default_headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except:
            return None
    
    def scrape(self, url, method='auto', wait_for_element=None, timeout=20, headers=None):
        if method == 'auto':
            html = self.scrape_with_requests(url, headers=headers, timeout=10)
            if html and len(html) > 1000:
                return html
            else:
                return self.scrape_with_selenium(url, wait_for_element, timeout)
        elif method == 'requests':
            return self.scrape_with_requests(url, headers=headers, timeout=timeout)
        elif method == 'selenium':
            return self.scrape_with_selenium(url, wait_for_element, timeout)
        else:
            return None
