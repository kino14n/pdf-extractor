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
    error_msg    = None

    if request.method == 'POST':
        f = request.files.get('pdf')
        if not f or not allowed_file(f.filename):
            error_msg = "Sube un PDF válido."
        else:
            filename = secure_filename(f.filename)
            path     = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(path)

            try:
                # 1) Leemos todo el texto y lo separamos en líneas
                lines = []
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        txt = page.extract_text()
                        if txt:
                            lines += txt.splitlines()

                datos   = []
                prev_qty = None

                # 2) Regex para línea que contenga cantidad y código juntos:
                re_qty_code = re.compile(r'^\s*(\d+)[x×]\s*([A-Za-z0-9][A-Za-z0-9:.\-]*)')
                # 3) Regex para línea que solo tenga cantidad:
                re_qty_only = re.compile(r'^\s*(\d+)[x×]\s*$')
                # 4) Regex para extraer código en línea siguiente:
                re_code     = re.compile(r'^\s*([A-Za-z0-9][A-Za-z0-9:.\-]*)')

                for raw in lines:
                    line = raw.strip()
                    if not line:
                        continue

                    # 2a) ¿Cantidad + código en la misma línea?
                    m = re_qty_code.match(line)
                    if m:
                        qty   = int(m.group(1))
                        code  = m.group(2)
                        datos.append({'codigo': code, 'cantidad': qty})
                        prev_qty = None
                        continue

                    # 2b) ¿Solo cantidad en esta línea?
                    m2 = re_qty_only.match(line)
                    if m2:
                        prev_qty = int(m2.group(1))
                        continue

                    # 2c) Si venimos de una línea con solo cantidad, extraemos código aquí
                    if prev_qty is not None:
                        m3 = re_code.match(line)
                        if m3:
                            code = m3.group(1)
                            datos.append({'codigo': code, 'cantidad': prev_qty})
                            prev_qty = None
                            continue
                        # si no coincide, dejamos prev_qty a la espera

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
