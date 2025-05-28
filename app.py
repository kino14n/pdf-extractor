import re
import os
import camelot
import pandas as pd
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

# Configuración
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(fn):
    return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET','POST'])
def index():
    tabla_html = None
    if request.method == 'POST':
        f = request.files.get('pdf')
        if not f or not allowed_file(f.filename):
            return render_template('index.html', error="Sube un PDF válido.")
        fn = secure_filename(f.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        f.save(path)

        # Extrae todas las tablas
        tablas = camelot.read_pdf(path, pages='all', flavor='stream')
        datos = []
        for t in tablas:
            df = t.df
            for _, row in df.iterrows():
                texto0 = row[0].strip()              # ej. "1x 2440-6 JOEFOX..."
                # 1) Cantidad: (\d+)x
                m1 = re.match(r'(\d+)x', texto0)
                if not m1:
                    continue
                cantidad = int(m1.group(1))

                # 2) Código: justo lo que sigue al 'x ' hasta el siguiente espacio
                m2 = re.match(r'\d+x\s+(\S+)', texto0)
                if not m2:
                    continue
                codigo = m2.group(1)

                datos.append({'codigo': codigo, 'cantidad': cantidad})

        # DataFrame sin agrupar
        df_raw = pd.DataFrame(datos, columns=['codigo','cantidad'])
        tabla_html = df_raw.to_html(index=False)

    return render_template('index.html', resumen_html=tabla_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
