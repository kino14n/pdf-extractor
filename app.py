import re
import os
import pandas as pd
import pdfplumber
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

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
        f = request.files.get('pdf')
        if not f or not allowed_file(f.filename):
            error_msg = "Sube un PDF válido."
        else:
            fn   = secure_filename(f.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
            f.save(path)

            try:
                # 1) Leemos todo el texto en líneas
                lines = []
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        txt = page.extract_text() or ""
                        lines += txt.splitlines()

                qty_pat = re.compile(r'^\s*(\d+)[x×]\s*$')
                datos   = []

                # 2) Para cada línea que solo tenga cantidad ("1x", "10×", etc.):
                for i, line in enumerate(lines):
                    m = qty_pat.match(line.strip())
                    if not m:
                        continue
                    cantidad = int(m.group(1))

                    # 3) El código siempre está en la LÍNEA SIGUIENTE antes del primer espacio
                    if i + 1 < len(lines):
                        next_line = lines[i+1].strip()
                        token = next_line.split()[0]
                        # Aseguramos que el token empiece por letra/dígito
                        if re.match(r'^[A-Za-z0-9]', token):
                            datos.append({'codigo': token, 'cantidad': cantidad})

                if not datos:
                    error_msg = "No se encontraron códigos con dos líneas de descripción."
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
