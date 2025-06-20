from flask import Flask, request, jsonify
from script import yarislari_cek
import pandas as pd

app = Flask(__name__)

@app.route("/veri", methods=["GET"])
def veri():
    tarih = request.args.get("tarih")
    sehir = request.args.get("sehir")

    if not tarih or not sehir:
        return jsonify({"hata": "Tarih ve şehir zorunludur."}), 400

    url = f"https://yenibeygir.com/{tarih}/{sehir}"
    kosular = yarislari_cek(url)

    if not kosular:
        return jsonify({"hata": "Koşu bulunamadı."}), 404

    json_veri = {
        str(kosu_no): df.to_dict(orient="records")
        for kosu_no, df in kosular.items()
    }

    return jsonify(json_veri)
