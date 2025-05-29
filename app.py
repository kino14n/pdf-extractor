import re
import os
import pandas as pd
import pdfplumber
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

# — Configuración —
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
    error_msg    = None

    if request.method == 'POST':
        fichero = request.files.get('pdf')
        if not fichero or not allowed_file(fichero.filename):
            error_msg = "Sube un PDF válido."
        else:
            nombre = secure_filename(fichero.filename)
            ruta   = os.path.join(app.config['UPLOAD_FOLDER'], nombre)
            fichero.save(ruta)

            try:
                # 1) Abrimos PDF y extraemos TODO el texto
                texto = ""
                with pdfplumber.open(ruta) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text() or ""
                        texto += t + "\n"

                # 2) Colapsamos saltos de línea y múltiples espacios
                texto = re.sub(r'\n+', ' ', texto)
                texto = re.sub(r'\s+', ' ', texto)

                # 3) Regex global: captura cantidad antes de x/× + código hasta el primer espacio
                patron = re.compile(r'(\d+)[x×]\s*([A-Za-z0-9][A-Za-z0-9:.\-]*)')
                matches = patron.findall(texto)

                if not matches:
                    error_msg = "No se hallaron códigos/cantidades en el PDF."
                else:
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
