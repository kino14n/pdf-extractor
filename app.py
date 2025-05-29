import re
import os
import pandas as pd
import pdfplumber
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

# Configuración
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(fn):
    return '.' in fn and fn.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET','POST'])
def index():
    resumen_html = None
    error_msg = None

    if request.method == 'POST':
        f = request.files.get('pdf')
        if not f or not allowed_file(f.filename):
            error_msg = "Sube un PDF válido."
        else:
            fn = secure_filename(f.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
            f.save(path)

            try:
                # 1) Extraer todo el texto del PDF
                texto = ""
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t:
                            texto += t + "\n"

                # 2) Normalizar: reemplazar saltos de línea y múltiples espacios por uno solo
                texto = re.sub(r'\s+', ' ', texto)

                # 3) Buscar pares (cantidad, código)
                regex = r'(\d+)[x×]\s*([A-Za-z0-9-]+)'
                matches = re.findall(regex, texto)

                if not matches:
                    error_msg = "No se hallaron códigos/cantidades en el PDF."
                else:
                    # Construir DataFrame
                    df = pd.DataFrame(matches, columns=['cantidad','codigo'])
                    df['cantidad'] = df['cantidad'].astype(int)
                    df = df[['codigo','cantidad']]
                    resumen_html = df.to_html(index=False)

            except Exception as e:
                error_msg = f"Error al procesar el PDF: {e}"

    return render_template('index.html',
                           resumen_html=resumen_html,
                           error=error_msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
