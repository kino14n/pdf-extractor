import re
import os
import pandas as pd
import pdfplumber
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

# —— Configuración básica ——
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
                # 1) Extraemos todas las líneas de texto
                lines = []
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t:
                            lines += t.splitlines()

                datos = []
                # Regex para línea que empieza con cantidad "1x", "10×", etc.
                # y captura cualquier secuencia de no-espacios como código
                patron = re.compile(r'^\s*(\d+)\s*[x×]\s*([^\s]+)')

                for raw in lines:
                    line = raw.strip()
                    if not line:
                        continue
                    m = patron.match(line)
                    if m:
                        cantidad = int(m.group(1))
                        codigo   = m.group(2)
                        datos.append({'codigo': codigo, 'cantidad': cantidad})

                if not datos:
                    error_msg = "No se hallaron códigos/cantidades en el PDF."
                else:
                    df = pd.DataFrame(datos, columns=['codigo','cantidad'])
                    resumen_html = df.to_html(index=False)

            except Exception as e:
                error_msg = f"Error al procesar el PDF: {e}"

    return render_template('index.html',
                           resumen_html=resumen_html,
                           error=error_msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
