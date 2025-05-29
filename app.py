import os, re
import camelot
import pandas as pd
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

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
    error = None

    if request.method == 'POST':
        f = request.files.get('pdf')
        if not f or not allowed_file(f.filename):
            error = "Sube un PDF válido."
        else:
            fn = secure_filename(f.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
            f.save(path)
            try:
                tablas = camelot.read_pdf(path, pages='all', flavor='stream')
                if not tablas:
                    tablas = camelot.read_pdf(path, pages='all', flavor='lattice')

                datos = []
                code_pat = re.compile(r'^[A-Za-z0-9][A-Za-z0-9:.\-]*$')
                qty_pat  = re.compile(r'^\s*(\d+)[x×]')

                for t in tablas:
                    df = t.df
                    n = len(df)
                    i = 0
                    while i < n:
                        row = df.iloc[i]
                        # 1) extraer cantidad
                        m_qty = qty_pat.match(str(row[0]))
                        if not m_qty:
                            i += 1
                            continue
                        cant = int(m_qty.group(1))

                        # 2) intenta extraer código de la misma fila
                        desc = str(row[1]).replace('\n',' ').strip()
                        tok = desc.split()[0] if desc.split() else ''
                        if code_pat.match(tok):
                            datos.append({'codigo': tok, 'cantidad': cant})
                            i += 1
                            continue

                        # 3) si no está, mira la siguiente fila
                        if i+1 < n:
                            next_desc = str(df.iloc[i+1,1]).replace('\n',' ').strip()
                            tok2 = next_desc.split()[0] if next_desc.split() else ''
                            if code_pat.match(tok2):
                                datos.append({'codigo': tok2, 'cantidad': cant})
                                i += 2
                                continue

                        # si no localiza, avanza sólo uno
                        i += 1

                if not datos:
                    error = "No se detectaron códigos ni cantidades."
                else:
                    out = pd.DataFrame(datos, columns=['codigo','cantidad'])
                    tabla_html = out.to_html(index=False)

            except Exception as e:
                error = f"Error al procesar el PDF: {e}"

    return render_template('index.html', resumen_html=tabla_html, error=error)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
