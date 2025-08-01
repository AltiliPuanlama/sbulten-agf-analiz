from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime

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
            "hazirlik_disiplini": 1,
            "toplam_puan": 6 + bias
        }

    total = len(galoplar)

    # Sprint Etkisi
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

    # Form Zamanlaması
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

    # Tempo Uyumu
    tempo_uyumu = min(5, int(sum(1 for g in galoplar if g['pist'] == 'Kum') / total * 5) + 1)

    # Toparlanma ve İstikrar
    toparlanma_istikrar = min(5, int(sum(1 for g in galoplar if g['tip'] in ['R', 'H']) / total * 5) + 1)

    # Jokey-İş Uyumu
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

    # Hazırlık Disiplini (Son 15 Gün)
    bugun = datetime.today()
    galop_tarihleri = []
    for g in galoplar:
        try:
            tarih = datetime.strptime(g['tarih'], "%d.%m.%Y")
            if (bugun - tarih).days <= 15:
                galop_tarihleri.append(tarih.date())
        except:
            continue
    tekil_gunler = sorted(set(galop_tarihleri))
    galop_sayisi = len(tekil_gunler)
    if galop_sayisi >= 6:
        hazirlik_disiplini = 5
    elif galop_sayisi >= 5:
        hazirlik_disiplini = 4
    elif galop_sayisi >= 4:
        hazirlik_disiplini = 3
    elif galop_sayisi >= 2:
        hazirlik_disiplini = 2
    else:
        hazirlik_disiplini = 1

    # Genel Seviye
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

    toplam_puan = round(
        sprint_etkisi + form_zamanlamasi + tempo_uyumu +
        toparlanma_istikrar + jokey_is_uyumu + genel_seviye + bias,
        2
    )

    return {
        "sprint_etkisi": sprint_etkisi,
        "form_zamanlamasi": form_zamanlamasi,
        "tempo_uyumu": tempo_uyumu,
        "toparlanma_istikrar": toparlanma_istikrar,
        "jokey_is_uyumu": jokey_is_uyumu,
        "genel_seviye": genel_seviye,
        "hazirlik_disiplini": hazirlik_disiplini,
        "toplam_puan": toplam_puan
    }

# (Diğer fonksiyonlar aynı kalıyor)

# render_template'de hazirlik_disiplini'yi göstermek için galop_sonuclari.html'ye de sütun eklersin.

