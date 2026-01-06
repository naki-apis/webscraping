from flask import Flask, render_template_string, request, jsonify, send_file
import os
import tempfile
import uuid
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = 'secret_key_here'

from tool import WebScraper

INDEX_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Web Scraper</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            background: #f5f5f5;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        input[type="text"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }
        .method-buttons {
            display: flex;
            gap: 10px;
            margin: 20px 0;
        }
        button {
            padding: 12px 25px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: background 0.3s;
        }
        .selenium-btn {
            background: #4CAF50;
            color: white;
        }
        .selenium-btn:hover {
            background: #45a049;
        }
        .requests-btn {
            background: #2196F3;
            color: white;
        }
        .requests-btn:hover {
            background: #0b7dda;
        }
        .advanced {
            background: #fff;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border: 1px solid #ddd;
        }
        .advanced-toggle {
            color: #666;
            cursor: pointer;
            user-select: none;
            padding: 5px 0;
        }
        .advanced-content {
            display: none;
            padding-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Web Scraper</h1>
        
        <form id="scrapeForm" action="/scrape" method="POST">
            <div class="form-group">
                <label for="url">URL para scrapear:</label>
                <input type="text" id="url" name="url" placeholder="https://ejemplo.com" required>
            </div>
            
            <div class="advanced">
                <div class="advanced-toggle" onclick="toggleAdvanced()">▼ Opciones avanzadas</div>
                <div class="advanced-content" id="advancedContent">
                    <div class="form-group">
                        <label for="wait_selector">Selector para esperar (Selenium):</label>
                        <input type="text" id="wait_selector" name="wait_selector" placeholder="div.content, #main, .post, //div[@class='content']">
                        <small>CSS, XPath, ID o Class selector</small>
                    </div>
                    <div class="form-group">
                        <label for="timeout">Timeout (segundos):</label>
                        <input type="number" id="timeout" name="timeout" value="20" min="5" max="120">
                    </div>
                </div>
            </div>
            
            <div class="method-buttons">
                <button type="button" onclick="submitForm('selenium')" class="selenium-btn">
                    Scrap con Selenium
                </button>
                <button type="button" onclick="submitForm('requests')" class="requests-btn">
                    Scrap con Requests
                </button>
            </div>
            
            <input type="hidden" name="method" id="method">
        </form>
    </div>
    
    <script>
        function submitForm(method) {
            document.getElementById('method').value = method;
            document.getElementById('scrapeForm').submit();
        }
        
        function toggleAdvanced() {
            const content = document.getElementById('advancedContent');
            const toggle = document.querySelector('.advanced-toggle');
            
            if (content.style.display === 'block') {
                content.style.display = 'none';
                toggle.innerHTML = '▼ Opciones avanzadas';
            } else {
                content.style.display = 'block';
                toggle.innerHTML = '▲ Opciones avanzadas';
            }
        }
        
        document.getElementById('url').focus();
    </script>
</body>
</html>
'''

ERROR_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Error</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            text-align: center;
        }
        .error-container {
            background: #ffebee;
            border: 1px solid #ffcdd2;
            border-radius: 10px;
            padding: 40px;
            margin: 20px 0;
        }
        .error-icon {
            font-size: 60px;
            color: #f44336;
            margin-bottom: 20px;
        }
        h1 {
            color: #d32f2f;
            margin-bottom: 20px;
        }
        .error-details {
            background: white;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            text-align: left;
        }
        .back-btn {
            display: inline-block;
            background: #4CAF50;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            font-size: 16px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">❌</div>
        <h1>Error en el Scraping</h1>
        
        <p>No se pudo obtener el contenido de la página solicitada.</p>
        
        <div class="error-details">
            <p><strong>URL:</strong> {{ url }}</p>
            <p><strong>Método:</strong> {{ method }}</p>
            <p><strong>Posibles causas:</strong></p>
            <ul>
                <li>La página requiere autenticación</li>
                <li>Cloudflare o protección anti-bots</li>
                <li>URL incorrecta o página no disponible</li>
                <li>Timeout excedido</li>
                <li>Problemas de red o conexión</li>
            </ul>
        </div>
        
        <a href="/" class="back-btn">Intentar de nuevo</a>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form.get('url')
    method = request.form.get('method')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    if method not in ['selenium', 'requests', 'auto']:
        method = 'auto'
    
    scraper = WebScraper()
    
    wait_element = None
    wait_selector = request.form.get('wait_selector')
    if wait_selector:
        if wait_selector.startswith(('//', './', '/')):
            from selenium.webdriver.common.by import By
            wait_element = (By.XPATH, wait_selector)
        elif wait_selector.startswith('#'):
            from selenium.webdriver.common.by import By
            wait_element = (By.ID, wait_selector[1:])
        elif wait_selector.startswith('.'):
            from selenium.webdriver.common.by import By
            wait_element = (By.CLASS_NAME, wait_selector[1:])
        else:
            from selenium.webdriver.common.by import By
            wait_element = (By.CSS_SELECTOR, wait_selector)
    
    timeout = int(request.form.get('timeout', 20))
    
    html_content = scraper.scrape(
        url=url,
        method=method,
        wait_for_element=wait_element,
        timeout=timeout
    )
    
    if html_content:
        session_id = str(uuid.uuid4())
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f'scraped_{session_id}.html')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_content
    
    else:
        return render_template_string(
            ERROR_HTML,
            url=url,
            method=method
        )

@app.route('/download/<session_id>')
def download(session_id):
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f'scraped_{session_id}.html')
    
    if os.path.exists(file_path):
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f'scraped_{session_id}.html',
            mimetype='text/html'
        )
    else:
        return 'File not found', 404

@app.route('/file/chrome')
def download_chrome():
    chrome_path = Path(__file__).parent.absolute() / "selenium" / "chrome"
    
    if chrome_path.exists():
        return send_file(
            str(chrome_path),
            as_attachment=True,
            download_name="chrome"
        )
    else:
        return "Chrome binary not found", 404

@app.route('/file/chromedriver')
def download_chromedriver():
    chromedriver_path = Path(__file__).parent.absolute() / "selenium" / "chromedriver"
    
    if chromedriver_path.exists():
        return send_file(
            str(chromedriver_path),
            as_attachment=True,
            download_name="chromedriver"
        )
    else:
        return "Chromedriver not found", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
