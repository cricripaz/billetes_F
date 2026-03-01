import os
import json
import re
import base64
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import easyocr

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# OCR
reader = easyocr.Reader(['en'], gpu=False)

# Cargar rangos correctamente
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RANGOS_PATH = os.path.join(BASE_DIR, "rangos.json")

with open(RANGOS_PATH) as f:
    rangos = json.load(f)

def es_prohibido(numero, corte):
    for r in rangos[corte]:
        if r["inicio"] <= numero <= r["fin"]:
            return True
    return False

def guardar_log(numero, corte, estado):
    df = pd.DataFrame([{
        "fecha": datetime.now(),
        "numero": numero,
        "corte": corte,
        "estado": estado
    }])
    df.to_csv("log.csv", mode="a", header=False, index=False)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/procesar_manual", methods=["POST"])
def procesar_manual():
    data = request.json
    numero = data["numero"]
    corte = data["corte"]

    if not numero.isdigit():
        return jsonify({"resultado": "Número inválido"})

    numero = int(numero)

    if es_prohibido(numero, corte):
        estado = "🚨 PROHIBIDO"
    else:
        estado = "✅ VALIDO"

    guardar_log(numero, corte, estado)

    return jsonify({
        "resultado": estado,
        "numero": numero
    })
@app.route("/procesar", methods=["POST"])
def procesar():
    data = request.json
    imagen_base64 = data["imagen"]
    corte = data["corte"]

    # Decodificar imagen
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
        if es_prohibido(numero_detectado, corte):
            estado = "🚨 PROHIBIDO"
        else:
            estado = "✅ VALIDO"

        guardar_log(numero_detectado, corte, estado)

        return jsonify({
            "resultado": estado,
            "numero": numero_detectado
        })

    return jsonify({"resultado": "No se detectó número válido"})
#test
if __name__ == "__main__":
    app.run(debug=True)