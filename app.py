import re
import os
import camelot
import pandas as pd
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

# Config
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(fn):
    return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET','POST'])
def index():
    resumen_html = None
    if request.method == 'POST':
        f = request.files.get('pdf')
        if not f or not allowed_file(f.filename):
            return render_template('index.html', error="Sube un PDF válido.")
        filename = secure_filename(f.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(path)

        # Extraer tablas
        tablas = camelot.read_pdf(path, pages='all', flavor='stream')
        datos = []
        for t in tablas:
            df = t.df
            for _, row in df.iterrows():
                m1 = re.match(r'(\d+)x', row[0].strip())
                if not m1: continue
                cantidad = int(m1.group(1))
                m2 = re.match(r'^(\S+)', row[1].strip())
                if not m2: continue
                codigo = m2.group(1)
                datos.append({'codigo': codigo, 'cantidad': cantidad})

        df = pd.DataFrame(datos)
        if not df.empty:
            resumen = df.groupby('codigo', as_index=False).sum()
        else:
            resumen = pd.DataFrame(columns=['codigo','cantidad'])
        resumen_html = resumen.to_html(index=False)

    return render_template('index.html', resumen_html=resumen_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
