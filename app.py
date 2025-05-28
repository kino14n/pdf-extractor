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

        datos = []
        tablas = camelot.read_pdf(path, pages='all', flavor='stream')
        for t in tablas:
            df = t.df
            for _, row in df.iterrows():
                # Unimos col0 y col1 para asegurar que capturemos cantidad + código juntos
                texto = f"{row[0].strip()} {row[1].strip()}"
                # 1) Buscar cantidad: dígitos antes de 'x'
                m_cant = re.search(r'(\d+)x', texto)
                if not m_cant:
                    continue
                cantidad = int(m_cant.group(1))
                # 2) Buscar código: lo que sigue al 'x ' hasta el siguiente espacio
                m_cod = re.search(r'\d+x\s+([A-Za-z0-9-]+)', texto)
                if not m_cod:
                    continue
                codigo = m_cod.group(1)
                datos.append({'codigo': codigo, 'cantidad': cantidad})

        df_raw = pd.DataFrame(datos, columns=['codigo','cantidad'])
        tabla_html = df_raw.to_html(index=False)

    return render_template('index.html', resumen_html=tabla_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
