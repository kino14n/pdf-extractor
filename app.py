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
            filename = secure_filename(f.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(path)

            try:
                # 1) Extraemos texto línea a línea
                lines = []
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        txt = page.extract_text()
                        if txt:
                            lines += txt.splitlines()

                datos = []
                prev_qty = None

                for raw in lines:
                    line = raw.strip()
                    if not line:
                        continue

                    # 2) ¿Cantidad en esta línea?
                    m_qty = re.match(r'(\d+)\s*[x×]', line)
                    if m_qty:
                        qty = int(m_qty.group(1))

                        # ¿Y el código en la misma línea?
                        m_code1 = re.search(r'[x×]\s*([A-Za-z0-9-]+)', line)
                        if m_code1:
                            datos.append({'codigo': m_code1.group(1), 'cantidad': qty})
                        else:
                            # No vino código: lo buscaremos en la siguiente línea
                            prev_qty = qty
                        continue

                    # 3) Si venimos con prev_qty, quizá esta línea tenga el código
                    if prev_qty is not None:
                        m_code2 = re.match(r'([A-Za-z0-9-]+)', line)
                        if m_code2:
                            datos.append({'codigo': m_code2.group(1), 'cantidad': prev_qty})
                            prev_qty = None
                            continue
                        # si no coincide, quizá sea descripción extra: seguimos buscando

                if not datos:
                    error_msg = "No se hallaron códigos/cantidades."
                else:
                    df = pd.DataFrame(datos, columns=['codigo','cantidad'])
                    resumen_html = df.to_html(index=False)

            except Exception as e:
                error_msg = f"Error procesando PDF: {e}"

    return render_template('index.html', resumen_html=resumen_html, error=error_msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
