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

RESULT_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Resultado del Scraping</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #333;
            color: white;
            padding: 15px 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .back-btn, .download-btn {
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
        }
        .download-btn {
            background: #2196F3;
        }
        .info {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .info-item {
            margin: 5px 0;
            padding: 5px;
            background: white;
            border-radius: 3px;
        }
        .html-preview {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.4;
            white-space: pre-wrap;
            max-height: 600px;
            overflow-y: auto;
        }
        .truncated {
            color: #888;
            font-style: italic;
            padding: 10px;
            text-align: center;
            background: #3d3d3d;
            border-radius: 3px;
            margin-top: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }
        .stat-box {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #2196F3;
        }
    </style>
</head>
<body>
    <div class="header">
        <a href="/" class="back-btn">← Nueva búsqueda</a>
        <h2>Resultado del Scraping</h2>
        <button onclick="downloadHTML()" class="download-btn">⬇ Guardar HTML</button>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-label">Método usado</div>
            <div class="stat-value">{{ method|upper }}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Caracteres</div>
            <div class="stat-value">{{ full_content_length }}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Sesión</div>
            <div class="stat-value">{{ session_id[:8] }}...</div>
        </div>
    </div>
    
    <div class="info">
        <div class="info-item"><strong>URL:</strong> {{ url }}</div>
        <div class="info-item"><strong>Método:</strong> {{ method }}</div>
        <div class="info-item"><strong>ID Sesión:</strong> {{ session_id }}</div>
    </div>
    
    <h3>Vista previa del HTML:</h3>
    <div class="html-preview">
        {{ html_content|safe }}
        {% if full_content_length > 5000 %}
        <div class="truncated">
            [Contenido truncado. El archivo completo se descargará con todos los {{ full_content_length }} caracteres]
        </div>
        {% endif %}
    </div>
    
    <script>
        function downloadHTML() {
            window.location.href = '/download/{{ session_id }}';
        }
        
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                downloadHTML();
            }
        });
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
        
        html_preview = html_content[:5000] + '...' if len(html_content) > 5000 else html_content
        
        return render_template_string(
            RESULT_HTML,
            html_content=html_preview,
            full_content_length=len(html_content),
            session_id=session_id,
            url=url,
            method=method
        )
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
