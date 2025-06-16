<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Extractor de Código y Cantidad</title>
  <style>
    body { font-family: sans-serif; padding: 2rem; background: #f0f2f5; }
    h1 { color: #005fa3; }
    form { margin-bottom: 1.5rem; }
    button { margin-left: 0.5rem; }
    table { border-collapse: collapse; width: 80%; max-width:600px; background: #fff; margin-top: 1rem; }
    th, td { border: 1px solid #ccc; padding: 0.5rem; text-align: center; }
    th { background: #0074D9; color: #fff; }
    .error { color: #c00; }
  </style>
</head>
<body>
  <h1>📑 Subir y Procesar PDF</h1>

  {% if error %}
    <p class="error">{{ error }}</p>
  {% endif %}

  <form method="post" enctype="multipart/form-data">
    <input type="file" name="pdf" accept="application/pdf" required>
    <button type="submit">Procesar</button>
    {% if resumen_html %}
      <button type="button" onclick="window.location.href='/'">Limpiar</button>
    {% endif %}
  </form>

  {% if resumen_html %}
    <p><strong>Total de códigos encontrados: {{ total }}</strong></p>
    <h2>📊 Todas las ocurrencias</h2>
    {{ resumen_html|safe }}
  {% endif %}
</body>
</html>
