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
                # Probar stream, luego lattice
                tablas = camelot.read_pdf(path, pages='all', flavor='stream')
                if not tablas:
                    tablas = camelot.read_pdf(path, pages='all', flavor='lattice')

                if not tablas:
                    error_msg = "No se encontraron tablas en el PDF."
                else:
                    datos = []
                    for t in tablas:
                        df = t.df
                        for fila in df.itertuples(index=False, name=None):
                            # Unimos todas las columnas de la fila
                            texto = " ".join(str(c).strip() for c in fila if c is not None)

                            # Extraer cantidad (número antes de 'x')
                            m1 = re.search(r'(\d+)x', texto)
                            # Extraer código (lo que sigue al 'x ' hasta espacio)
                            m2 = re.search(r'\d+x\s+([A-Za-z0-9-]+)', texto)

                            if m1 and m2:
                                datos.append({
                                    'codigo': m2.group(1),
                                    'cantidad': int(m1.group(1))
                                })

                    if not datos:
                        error_msg = "No se hallaron códigos/cantidades en las tablas."
                    else:
                        df_raw = pd.DataFrame(datos, columns=['codigo','cantidad'])
                        resumen_html = df_raw.to_html(index=False)

            except Exception as e:
                error_msg = f"Error al procesar el PDF: {e}"

    return render_template('index.html',
                           resumen_html=resumen_html,
                           error=error_msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
