import os
import json
import re
import base64
from flask import Flask, render_template, request, jsonify
import easyocr

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

reader = None

# ==============================
# CARGAR RANGOS
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RANGOS_PATH = os.path.join(BASE_DIR, "rangos.json")

with open(RANGOS_PATH) as f:
    rangos = json.load(f)

# ==============================
# FUNCIONES
# ==============================
def es_prohibido(numero, corte):
    if corte not in rangos:
        return False

    for r in rangos[corte]:
        if r["inicio"] <= numero <= r["fin"]:
            return True
    return False

# ==============================
# RUTAS
# ==============================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/procesar_manual", methods=["POST"])
def procesar_manual():
    data = request.json
    numero = data.get("numero")
    corte = data.get("corte")

    if not numero or not numero.isdigit():
        return jsonify({"resultado": "Número inválido"})

    numero = int(numero)

    estado = "🚨 PROHIBIDO" if es_prohibido(numero, corte) else "✅ VALIDO"

    return jsonify({
        "resultado": estado,
        "numero": numero
    })


@app.route("/procesar", methods=["POST"])
def procesar():
    global reader

    data = request.json
    imagen_base64 = data.get("imagen")
    corte = data.get("corte")

    if not imagen_base64:
        return jsonify({"resultado": "Imagen inválida"})

    if reader is None:
        reader = easyocr.Reader(['en'], gpu=False)

    imagen_bytes = base64.b64decode(imagen_base64.split(",")[1])
    ruta = os.path.join(UPLOAD_FOLDER, "captura.jpg")

    with open(ruta, "wb") as f:
        f.write(imagen_bytes)

    resultados = reader.readtext(ruta)

    numero_detectado = None

    for (_, text, prob) in resultados:
        match = re.search(r'\d{7,9}', text)
        if match:
            numero_detectado = int(match.group())
            break

    if numero_detectado:
        estado = "🚨 PROHIBIDO" if es_prohibido(numero_detectado, corte) else "✅ VALIDO"
        return jsonify({
            "resultado": estado,
            "numero": numero_detectado
        })

    return jsonify({"resultado": "No se detectó número válido"})


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
