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
            flex-wrap: wrap;
        }
        button {
            padding: 12px 25px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: background 0.3s;
            margin: 5px;
            flex: 1;
            min-width: 180px;
        }
        .selenium-btn {
            background: #4CAF50;
            color: white;
        }
        .selenium-btn:hover {
            background: #45a049;
        }
        .selenium-full-btn {
            background: #2E7D32;
            color: white;
        }
        .selenium-full-btn:hover {
            background: #1B5E20;
        }
        .requests-btn {
            background: #2196F3;
            color: white;
        }
        .requests-btn:hover {
            background: #0b7dda;
        }
        .screenshot-btn {
            background: #FF9800;
            color: white;
        }
        .screenshot-btn:hover {
            background: #F57C00;
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
        .download-section {
            background: #e8f5e9;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
            text-align: center;
            border: 1px solid #c8e6c9;
        }
        .download-btn {
            background: #4CAF50;
            color: white;
            padding: 15px 30px;
            border-radius: 5px;
            text-decoration: none;
            display: inline-block;
            margin: 10px;
            font-weight: bold;
        }
        .download-btn:hover {
            background: #388E3C;
        }
        .screenshot-preview {
            text-align: center;
            margin: 20px 0;
        }
        .screenshot-img {
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
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
                        <input type="number" id="timeout" name="timeout" value="30" min="5" max="120">
                    </div>
                </div>
            </div>
            
            <div class="method-buttons">
                <button type="button" onclick="submitForm('selenium_full')" class="selenium-full-btn">
                    📦 Selenium + HTML.ZIP
                </button>
                <button type="button" onclick="submitForm('screenshot')" class="screenshot-btn">
                    📸 Captura de Pantalla
                </button>
                <button type="button" onclick="submitForm('selenium')" class="selenium-btn">
                    Selenium
                </button>
                <button type="button" onclick="submitForm('requests')" class="requests-btn">
                    Requests
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

RESULT_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Scraping Completado</title>
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
        .success-icon {
            font-size: 60px;
            color: #4CAF50;
            text-align: center;
            margin-bottom: 20px;
        }
        .info-box {
            background: white;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .download-section {
            background: #e8f5e9;
            padding: 30px;
            border-radius: 5px;
            margin: 30px 0;
            text-align: center;
            border: 1px solid #c8e6c9;
        }
        .download-btn {
            background: #4CAF50;
            color: white;
            padding: 15px 40px;
            border-radius: 5px;
            text-decoration: none;
            display: inline-block;
            margin: 10px;
            font-size: 18px;
            font-weight: bold;
            transition: background 0.3s;
        }
        .download-btn:hover {
            background: #388E3C;
        }
        .screenshot-btn {
            background: #FF9800;
            color: white;
            padding: 15px 40px;
            border-radius: 5px;
            text-decoration: none;
            display: inline-block;
            margin: 10px;
            font-size: 18px;
            font-weight: bold;
            transition: background 0.3s;
        }
        .screenshot-btn:hover {
            background: #F57C00;
        }
        .preview-section {
            background: white;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .back-btn {
            display: inline-block;
            background: #2196F3;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            font-size: 16px;
            margin-top: 20px;
        }
        .back-btn:hover {
            background: #0b7dda;
        }
        .screenshot-preview {
            text-align: center;
            margin: 20px 0;
        }
        .screenshot-img {
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">✅</div>
        <h1>Scraping Completado</h1>
        
        <div class="info-box">
            <p><strong>URL:</strong> {{ url }}</p>
            <p><strong>Método:</strong> {{ method }}</p>
            {% if resource_count is defined %}
            <p><strong>Recursos descargados:</strong> {{ resource_count }}</p>
            <p><strong>Tamaño del archivo:</strong> {{ file_size }}</p>
            {% endif %}
        </div>
        
        {% if method == 'Selenium + HTML.ZIP' %}
        <div class="download-section">
            <h3>📦 Archivo HTML.ZIP listo para descargar</h3>
            <p>Este archivo contiene la página web completa con todos los recursos:</p>
            <ul style="text-align: left; display: inline-block;">
                <li>HTML de la página</li>
                <li>Archivos CSS</li>
                <li>Scripts JavaScript</li>
                <li>Imágenes y recursos multimedia</li>
                <li>Fuentes y iconos</li>
            </ul>
            <br><br>
            <a href="/download_zip/{{ session_id }}" class="download-btn">
                ⬇️ Descargar HTML.ZIP
            </a>
        </div>
        {% elif method == 'Captura de Pantalla' %}
        <div class="download-section">
            <h3>📸 Captura de Pantalla</h3>
            <p>Captura completa de la página web:</p>
            
            {% if screenshot_preview %}
            <div class="screenshot-preview">
                <img src="data:image/png;base64,{{ screenshot_preview }}" alt="Captura de pantalla" class="screenshot-img">
            </div>
            {% endif %}
            
            <br>
            <a href="/download_screenshot/{{ session_id }}" class="screenshot-btn">
                ⬇️ Descargar Captura (PNG)
            </a>
            <a href="/download/{{ session_id }}" class="download-btn">
                📄 Descargar HTML
            </a>
        </div>
        {% else %}
        <div class="download-section">
            <h3>📄 Contenido HTML obtenido</h3>
            <a href="/download/{{ session_id }}" class="download-btn">
                ⬇️ Descargar HTML
            </a>
        </div>
        {% endif %}
        
        {% if html_preview %}
        <div class="preview-section">
            <h3>Vista previa del HTML:</h3>
            <textarea style="width: 100%; height: 200px; font-family: monospace; padding: 10px;" readonly>{{ html_preview }}</textarea>
        </div>
        {% endif %}
        
        <div style="text-align: center;">
            <a href="/" class="back-btn">Scrapear otra página</a>
        </div>
    </div>
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
    
    if method not in ['selenium', 'requests', 'auto', 'selenium_full', 'screenshot']:
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
    
    timeout = int(request.form.get('timeout', 30))
    
    if method == 'selenium_full':
        result = scraper.scrape(
            url=url,
            method=method,
            wait_for_element=wait_element,
            timeout=timeout
        )
        
        if result and result[0] and result[1]:
            html_content, zip_path, _ = result
            session_id = str(uuid.uuid4())
            
            zip_files[session_id] = zip_path
            
            try:
                file_size = os.path.getsize(zip_path)
                if file_size < 1024:
                    file_size_str = f"{file_size} bytes"
                elif file_size < 1024 * 1024:
                    file_size_str = f"{file_size/1024:.1f} KB"
                else:
                    file_size_str = f"{file_size/(1024*1024):.1f} MB"
            except:
                file_size_str = "N/A"
            
            resource_count = len(scraper.scraped_resources)
            
            html_preview = html_content + "..." if len(html_content) > 2000 else html_content
            
            return render_template_string(
                RESULT_HTML,
                url=url,
                method="Selenium + HTML.ZIP",
                session_id=session_id,
                resource_count=resource_count,
                file_size=file_size_str,
                html_preview=html_preview
            )
        else:
            return render_template_string(
                ERROR_HTML,
                url=url,
                method=method
            )
    
    elif method == 'screenshot':
        result = scraper.scrape(
            url=url,
            method=method,
            wait_for_element=wait_element,
            timeout=timeout
        )
        
        if result and result[0] and result[1]:
            html_content, screenshot_data = result
            session_id = str(uuid.uuid4())
            
            screenshot_files[session_id] = screenshot_data
            
            temp_dir = tempfile.gettempdir()
            html_path = os.path.join(temp_dir, f'scraped_{session_id}.html')
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            html_files[session_id] = html_path
            
            import base64
            screenshot_preview = base64.b64encode(screenshot_data).decode('utf-8') if screenshot_data else ""
            
            html_preview = html_content + "..." if len(html_content) > 2000 else html_content
            
            return render_template_string(
                RESULT_HTML,
                url=url,
                method="Captura de Pantalla",
                session_id=session_id,
                html_preview=html_preview,
                screenshot_preview=screenshot_preview
            )
        else:
            return render_template_string(
                ERROR_HTML,
                url=url,
                method=method
            )
    
    else:
        result = scraper.scrape(
            url=url,
            method=method,
            wait_for_element=wait_element,
            timeout=timeout
        )
        
        if result and result[0]:
            html_content = result[0] if isinstance(result, tuple) else result
            session_id = str(uuid.uuid4())
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f'scraped_{session_id}.html')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            html_files[session_id] = file_path
            
            html_preview = html_content + "..." if len(html_content) > 2000 else html_content
            
            method_name = "Selenium" if method == 'selenium' else "Requests" if method == 'requests' else "Auto"
            
            return render_template_string(
                RESULT_HTML,
                url=url,
                method=method_name,
                session_id=session_id,
                html_preview=html_preview
            )
        
        else:
            return render_template_string(
                ERROR_HTML,
                url=url,
                method=method
            )

zip_files = {}
screenshot_files = {}
html_files = {}

@app.route('/download_zip/<session_id>')
def download_zip(session_id):
    if session_id in zip_files:
        zip_path = zip_files[session_id]
        if os.path.exists(zip_path):
            filename = os.path.basename(zip_path)
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/zip'
            )
    
    return 'File not found', 404

@app.route('/download_screenshot/<session_id>')
def download_screenshot(session_id):
    if session_id in screenshot_files:
        screenshot_data = screenshot_files[session_id]
        if screenshot_data:
            import io
            from flask import make_response
            
            response = make_response(screenshot_data)
            response.headers.set('Content-Type', 'image/png')
            response.headers.set('Content-Disposition', 'attachment', filename=f'screenshot_{session_id}.png')
            return response
    
    return 'File not found', 404

@app.route('/download/<session_id>')
def download(session_id):
    if session_id in html_files:
        file_path = html_files[session_id]
        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=f'scraped_{session_id}.html',
                mimetype='text/html'
            )
    
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
