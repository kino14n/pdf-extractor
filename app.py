import re
import os
import pandas as pd
import pdfplumber
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

# Configuración básica
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    resumen_html = None
    error_msg = None
    total_codes = 0

    if request.method == 'POST':
        f = request.files.get('pdf')
        if not f or not allowed_file(f.filename):
            error_msg = "Sube un PDF válido."
        else:
            filename = secure_filename(f.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(path)

            try:
                datos = []
                # Patrón para cantidad (ej. "10x" o "10×")
                qty_pat  = re.compile(r'^(\d+)[x×]$')
                # Patrón para código válido
                code_pat = re.compile(r'^[A-Za-z0-9][A-Za-z0-9:.\-]*$')

                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        words = page.extract_words(use_text_flow=True)
                        for idx, w in enumerate(words):
                            m = qty_pat.match(w['text'])
                            if m and idx + 1 < len(words):
                                cantidad = int(m.group(1))
                                codigo   = words[idx+1]['text']
                                if code_pat.match(codigo):
                                    datos.append({'codigo': codigo, 'cantidad': cantidad})

                if not datos:
                    error_msg = "No se hallaron códigos/cantidades en el PDF."
                else:
                    # Número total de códigos extraídos (ocurrencias)
                    total_codes = len(datos)
                    # Agrupar por código y sumar cantidades por código
                    df = pd.DataFrame(datos)
                    df_grouped = df.groupby('codigo', as_index=False)['cantidad'].sum()
                    # Generar tabla HTML con los totales por código
                    resumen_html = df_grouped.to_html(index=False)

            except Exception as e:
                error_msg = f"Error al procesar el PDF: {e}"

    return render_template(
        'index.html',
        resumen_html=resumen_html,
        error=error_msg,
        total_codes=total_codes
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
