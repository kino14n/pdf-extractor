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
    total        = 0

    if request.method == 'POST':
        f = request.files.get('pdf')
        if not f or not allowed_file(f.filename):
            error_msg = "Sube un PDF válido."
        else:
            fn   = secure_filename(f.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
            f.save(path)

            try:
                # 1) Extraemos todas las líneas de texto, en orden
                lines = []
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        txt = page.extract_text() or ""
                        lines += txt.splitlines()

                # 2) Patrones
                combined_pat = re.compile(r'^\s*(\d+)[x×]\s*([A-Za-z0-9][A-Za-z0-9:.\-]*)')
                qty_only_pat = re.compile(r'^\s*(\d+)[x×]\s*$')
                code_pat     = re.compile(r'^[A-Za-z0-9][A-Za-z0-9:.\-]*$')

                datos = []
                i = 0
                n = len(lines)
                while i < n:
                    line = lines[i].strip()

                    # 2a) Cantidad + código en la MISMA línea
                    m1 = combined_pat.match(line)
                    if m1:
                        cantidad = int(m1.group(1))
                        codigo   = m1.group(2)
                        datos.append({'codigo': codigo, 'cantidad': cantidad})
                        i += 1
                        continue

                    # 2b) Sólo cantidad → buscar código en la línea siguiente
                    m2 = qty_only_pat.match(line)
                    if m2 and i + 1 < n:
                        cantidad  = int(m2.group(1))
                        next_line = lines[i+1].strip()
                        token     = next_line.split()[0] if next_line.split() else ''
                        if code_pat.match(token):
                            datos.append({'codigo': token, 'cantidad': cantidad})
                        i += 2
                        continue

                    i += 1

                total = len(datos)
                if total == 0:
                    error_msg = "No se hallaron códigos/cantidades en el PDF."
                else:
                    df = pd.DataFrame(datos, columns=['codigo','cantidad'])
                    resumen_html = df.to_html(index=False)

            except Exception as e:
                error_msg = f"Error al procesar el PDF: {e}"

    return render_template('index.html',
                           resumen_html=resumen_html,
                           error=error_msg,
                           total=total)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
