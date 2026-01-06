import time
import random
import requests
import os
import zipfile
import base64
from pathlib import Path
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup

class WebScraper:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.absolute()
        self.selenium_dir = self.base_dir / "selenium"
        self.session = requests.Session()
        self.driver = None
        self.scraped_resources = {}
    
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
    
    def _download_resource(self, url, resource_type, output_dir):
        try:
            parsed_url = urlparse(url)
            if not parsed_url.netloc:
                return None
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                content = response.content
                
                path = parsed_url.path
                if not path or path == '/':
                    filename = 'index'
                else:
                    filename = os.path.basename(path)
                    if not filename:
                        filename = 'index'
                
                ext_map = {
                    'css': '.css',
                    'js': '.js',
                    'image': '.jpg',
                    'font': '.woff2'
                }
                
                if '.' not in filename:
                    ext = ext_map.get(resource_type, '.bin')
                    filename += ext
                
                filepath = output_dir / filename
                
                counter = 1
                while filepath.exists():
                    name_parts = filename.rsplit('.', 1)
                    if len(name_parts) == 2:
                        new_filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                    else:
                        new_filename = f"{filename}_{counter}"
                    filepath = output_dir / new_filename
                    counter += 1
                
                with open(filepath, 'wb') as f:
                    f.write(content)
                
                return filepath.name
            return None
        except:
            return None
    
    def _extract_resources(self, html_content, base_url, output_dir):
        soup = BeautifulSoup(html_content, 'html.parser')
        resources = []
        
        css_tags = soup.find_all('link', rel='stylesheet')
        for tag in css_tags:
            if tag.get('href'):
                resources.append(('css', urljoin(base_url, tag['href'])))
        
        script_tags = soup.find_all('script', src=True)
        for tag in script_tags:
            resources.append(('js', urljoin(base_url, tag['src'])))
        
        img_tags = soup.find_all('img', src=True)
        for tag in img_tags:
            resources.append(('image', urljoin(base_url, tag['src'])))
        
        link_tags = soup.find_all('link', href=True)
        for tag in link_tags:
            href = tag.get('href')
            if href and any(href.endswith(ext) for ext in ['.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']):
                resources.append(('image', urljoin(base_url, href)))
        
        video_tags = soup.find_all('video', src=True)
        for tag in video_tags:
            resources.append(('image', urljoin(base_url, tag['src'])))
        
        source_tags = soup.find_all('source', src=True)
        for tag in source_tags:
            resources.append(('image', urljoin(base_url, tag['src'])))
        
        for resource_type, url in resources:
            if url not in self.scraped_resources:
                filename = self._download_resource(url, resource_type, output_dir)
                if filename:
                    self.scraped_resources[url] = filename
                    
                    if resource_type == 'css':
                        try:
                            with open(output_dir / filename, 'r', encoding='utf-8') as f:
                                css_content = f.read()
                            
                            import re
                            url_pattern = r'url\([\'"]?([^\)\'"]+)[\'"]?\)'
                            css_urls = re.findall(url_pattern, css_content)
                            
                            for css_url in css_urls:
                                full_css_url = urljoin(url, css_url)
                                if full_css_url not in self.scraped_resources:
                                    css_filename = self._download_resource(full_css_url, 'image', output_dir)
                                    if css_filename:
                                        self.scraped_resources[full_css_url] = css_filename
                        except:
                            pass
        
        return soup
    
    def _modify_html_for_local(self, soup, output_dir):
        for tag in soup.find_all(['link', 'script', 'img', 'video', 'source']):
            url_attr = 'href' if tag.name == 'link' else 'src'
            
            if tag.get(url_attr):
                original_url = tag[url_attr]
                
                for scraped_url, filename in self.scraped_resources.items():
                    if original_url in scraped_url or scraped_url.endswith(original_url):
                        tag[url_attr] = filename
                        break
        
        for tag in soup.find_all('style'):
            if tag.string:
                css_text = tag.string
                import re
                url_pattern = r'url\([\'"]?([^\)\'"]+)[\'"]?\)'
                
                def replace_url(match):
                    url = match.group(1)
                    for scraped_url, filename in self.scraped_resources.items():
                        if url in scraped_url or scraped_url.endswith(url):
                            return f'url({filename})'
                    return match.group(0)
                
                modified_css = re.sub(url_pattern, replace_url, css_text)
                tag.string = modified_css
        
        return str(soup)
    
    def take_screenshot(self, url, wait_for_element=None, timeout=30):
        if not self._create_driver():
            return None, None
        
        try:
            self.driver.get(url)
            time.sleep(random.uniform(3, 5))
            
            self._wait_for_cloudflare()
            
            if wait_for_element:
                by, selector = wait_for_element
                try:
                    WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((by, selector))
                    )
                except TimeoutException:
                    pass
            
            time.sleep(random.uniform(2, 4))
            
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            screenshot_data = b""
            
            if total_height <= viewport_height * 1.5:
                screenshot = self.driver.get_screenshot_as_png()
                screenshot_data = screenshot
            else:
                screenshots = []
                for i in range(0, total_height, viewport_height):
                    self.driver.execute_script(f"window.scrollTo(0, {i});")
                    time.sleep(0.5)
                    screenshot = self.driver.get_screenshot_as_png()
                    screenshots.append(screenshot)
                
                screenshot_data = screenshots[0] if screenshots else b""
            
            html_content = self.driver.page_source
            
            return html_content, screenshot_data
            
        except Exception as e:
            return None, None
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                except:
                    pass
    
    def scrape_with_selenium_full(self, url, wait_for_element=None, timeout=30):
        if not self._create_driver():
            return None, None, None
        
        try:
            self.driver.get(url)
            time.sleep(random.uniform(3, 5))
            
            self._wait_for_cloudflare()
            
            if wait_for_element:
                by, selector = wait_for_element
                try:
                    WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((by, selector))
                    )
                except TimeoutException:
                    pass
            
            time.sleep(random.uniform(2, 4))
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 2))
            
            html_content = self.driver.page_source
            
            temp_dir = Path(tempfile.gettempdir()) / f"scrape_{int(time.time())}"
            temp_dir.mkdir(exist_ok=True)
            
            soup = self._extract_resources(html_content, url, temp_dir)
            
            modified_html = self._modify_html_for_local(soup, temp_dir)
            
            html_path = temp_dir / "index.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(modified_html)
            
            zip_path = Path(tempfile.gettempdir()) / f"webpage_{int(time.time())}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(temp_dir)
                        zipf.write(file_path, arcname)
            
            import shutil
            shutil.rmtree(temp_dir)
            
            return html_content, str(zip_path), None
            
        except Exception as e:
            return None, None, None
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                except:
                    pass
    
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
                return html, None, None
            else:
                return self.scrape_with_selenium(url, wait_for_element, timeout), None, None
        elif method == 'requests':
            return self.scrape_with_requests(url, headers=headers, timeout=timeout), None, None
        elif method == 'selenium':
            return self.scrape_with_selenium(url, wait_for_element, timeout), None, None
        elif method == 'selenium_full':
            return self.scrape_with_selenium_full(url, wait_for_element, timeout)
        elif method == 'screenshot':
            return self.take_screenshot(url, wait_for_element, timeout)
        else:
            return None, None, None
