from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from collections import Counter

app = Flask(__name__)

def galop_detay_analiz(galoplar, bias):
    if not galoplar:
        return {
            "sprint_etkisi": 1,
            "form_zamanlamasi": 1,
            "tempo_uyumu": 1,
            "toparlanma_istikrar": 1,
            "jokey_is_uyumu": 1,
            "genel_seviye": 1,
            "toplam_puan": 6 + bias
        }

    total = len(galoplar)

    sprint_values = []
    for g in galoplar:
        try:
            sprint = float(g['sprint'].replace(',', '.'))
            sprint_values.append(sprint)
        except:
            continue
    if sprint_values:
        avg_sprint = sum(sprint_values) / len(sprint_values)
        if avg_sprint <= 25.0:
            sprint_etkisi = 5
        elif avg_sprint <= 26.0:
            sprint_etkisi = 4
        elif avg_sprint <= 27.0:
            sprint_etkisi = 3
        elif avg_sprint <= 28.0:
            sprint_etkisi = 2
        else:
            sprint_etkisi = 1
    else:
        sprint_etkisi = 1

    iyi_sure = [g for g in galoplar if g['sure'] and ('1.00' <= g['sure'] <= '1.04.5')]
    oran = len(iyi_sure) / total if total else 0
    if oran >= 0.8:
        form_zamanlamasi = 5
    elif oran >= 0.6:
        form_zamanlamasi = 4
    elif oran >= 0.4:
        form_zamanlamasi = 3
    elif oran >= 0.2:
        form_zamanlamasi = 2
    else:
        form_zamanlamasi = 1

    tempo_uyumu = min(5, int(sum(1 for g in galoplar if g['pist'] == 'Kum') / total * 5) + 1)
    toparlanma_istikrar = min(5, int(sum(1 for g in galoplar if g['tip'] in ['R', 'H']) / total * 5) + 1)

    jokeyler = [g['galop_jokey'] for g in galoplar if g['galop_jokey']]
    if not jokeyler:
        jokey_is_uyumu = 1
    else:
        sayim = Counter(jokeyler)
        oran = sayim.most_common(1)[0][1] / total
        if oran >= 0.8:
            jokey_is_uyumu = 5
        elif oran >= 0.6:
            jokey_is_uyumu = 4
        elif oran >= 0.4:
            jokey_is_uyumu = 3
        elif oran >= 0.2:
            jokey_is_uyumu = 2
        else:
            jokey_is_uyumu = 1

    genel_seviye = 1
    if total >= 6:
        genel_seviye += 1
    if any(g['sure'] and g['sure'] < '1.03.0' for g in galoplar):
        genel_seviye += 1
    if any(g['sprint'] and float(g['sprint'].replace(',', '.')) < 25.5 for g in galoplar):
        genel_seviye += 1
    if sum(1 for g in galoplar if g['tip'] in ['R', 'H']) / total >= 0.5:
        genel_seviye += 1
    genel_seviye = min(genel_seviye, 5)

    toplam_puan = round(sprint_etkisi + form_zamanlamasi + tempo_uyumu + toparlanma_istikrar + jokey_is_uyumu + genel_seviye + bias, 2)

    return {
        "sprint_etkisi": sprint_etkisi,
        "form_zamanlamasi": form_zamanlamasi,
        "tempo_uyumu": tempo_uyumu,
        "toparlanma_istikrar": toparlanma_istikrar,
        "jokey_is_uyumu": jokey_is_uyumu,
        "genel_seviye": genel_seviye,
        "toplam_puan": toplam_puan
    }

def veri_cek_ve_analiz_et(link, kosu_no):
    response = requests.get(link)
    soup = BeautifulSoup(response.content, 'html.parser')
    tum_satirlar = soup.find_all("tr")

    kosu_sonuclari = {
        "kosu": f"{kosu_no}. Koşu",
        "atlar": []
    }

    index = 0
    bias_step = 0.00001
    bias_value = 0

    while index < len(tum_satirlar):
        satir = tum_satirlar[index]
        if satir.find("td", class_="g"):
            td = satir.find("td", class_="g")
            at_ismi_tag = td.find("a", class_="atisimlink")
            if not at_ismi_tag:
                index += 1
                continue

            at_ismi = at_ismi_tag.text.strip()
            galoplar = []
            index += 1

            while index < len(tum_satirlar) and not tum_satirlar[index].find("td", class_="g"):
                tds = tum_satirlar[index].find_all("td")
                if len(tds) >= 12:
                    galop = {
                        "tarih": tds[0].text.strip(),
                        "il": tds[1].text.strip(),
                        "galop_jokey": tds[3].text.strip(),
                        "sprint": tds[4].text.strip(),
                        "sure": tds[7].text.strip(),
                        "tip": tds[10].text.strip(),
                        "pist": tds[11].text.strip()
                    }
                    galoplar.append(galop)
                index += 1

            analiz = galop_detay_analiz(galoplar, bias_value)
            bias_value += bias_step

            analiz["at_ismi"] = at_ismi
            analiz["detay"] = {
                "sprint_etkisi": analiz["sprint_etkisi"],
                "form_zamanlamasi": analiz["form_zamanlamasi"],
                "tempo_uyumu": analiz["tempo_uyumu"],
                "toparlanma_istikrar": analiz["toparlanma_istikrar"],
                "jokey_is_uyumu": analiz["jokey_is_uyumu"],
                "genel_seviye": analiz["genel_seviye"]
            }
            kosu_sonuclari["atlar"].append(analiz)
        else:
            index += 1

    kosu_sonuclari["atlar"] = sorted(kosu_sonuclari["atlar"], key=lambda x: x["toplam_puan"], reverse=True)

    return kosu_sonuclari

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analiz', methods=['POST'])
def analiz():
    tum_kosular = []
    for i in range(1, 11):
        link = request.form.get(f'link{i}')
        if link:
            sonuc = veri_cek_ve_analiz_et(link, i)
            tum_kosular.append(sonuc)

    return render_template('galop_sonuclari.html', tum_kosular=tum_kosular)

# 🔥 Flask'ı dış dünyaya açmak için Render'a uygun hale getiriyoruz
if __name__ != '__main__':
    import logging
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
