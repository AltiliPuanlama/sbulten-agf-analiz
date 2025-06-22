import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re

st.set_page_config(layout="wide")
st.title("Trakus Verileri Analiz Paneli")

url = st.text_input("Trakus Sayfası URL'si", placeholder="Örn: http://91.151.93.198:5001/20250622/ADANA")
baslat = st.button("Analiz Et")

def extract_time(s):
    try:
        dakika, saniye = s.strip().split(":")
        return int(dakika) * 60 + float(saniye)
    except:
        return None

def calculate_tempo_score(times):
    deltas = [t2 - t1 for t1, t2 in zip(times[:-1], times[1:]) if t1 is not None and t2 is not None]
    if len(deltas) < 2:
        return 0
    if all(abs(deltas[i] - deltas[i-1]) < 0.5 for i in range(1, len(deltas))):
        return 10  # sabit tempo
    elif deltas[-1] < deltas[0]:
        return 7   # atak yapmış
    else:
        return 4   # zayıf tempo

def calculate_leader_bonus(rows):
    liderlik_skoru = {row["At Adı"]: 0 for row in rows}
    mesafeler = ["200m", "400m", "600m", "800m", "1000m", "1200m"]
    for mesafe in mesafeler:
        sureler = [(row["At Adı"], extract_time(row.get(mesafe, "-"))) for row in rows]
        sureler = [(a, t) for a, t in sureler if t is not None]
        if sureler:
            lider = min(sureler, key=lambda x: x[1])[0]
            liderlik_skoru[lider] += 1

    for k, v in liderlik_skoru.items():
        if v >= len(mesafeler):  # tüm mesafelerde liderse
            liderlik_skoru[k] = 15
        else:
            liderlik_skoru[k] = 0
    return liderlik_skoru

def analiz_tablosu(kosu_adi, rows):
    df = pd.DataFrame(rows)
    liderlik_bonusu = calculate_leader_bonus(rows)

    analiz_listesi = []
    for _, row in df.iterrows():
        try:
            max_hiz = float(row["MAKSİMUM HIZ"])
            ort_hiz = float(row["ORTALAMA HIZ"])
        except:
            max_hiz = ort_hiz = 0

        tempo_times = [extract_time(row.get(m, "-")) for m in ["200m", "400m", "600m", "800m", "1000m", "1200m"]]
        tempo_puani = calculate_tempo_score(tempo_times)

        cikis = extract_time(row.get("200m", "-"))
        cikis_puan = 5 if cikis and cikis < 15 else 2 if cikis else 0

        final_ivme = 10 if tempo_times[-1] and tempo_times[0] and tempo_times[-1] < tempo_times[0] else 0
        lider_bonus = liderlik_bonusu.get(row["At Adı"], 0)

        puan = (max_hiz * 2) + (ort_hiz * 1.5) + tempo_puani + final_ivme + cikis_puan + lider_bonus
        analiz_listesi.append({
            "At Adı": row["At Adı"],
            "Max Hız": max_hiz,
            "Ort Hız": ort_hiz,
            "Tempo Puanı": tempo_puani,
            "Final İvme": final_ivme,
            "Çıkış": cikis_puan,
            "Liderlik": lider_bonus,
            "Toplam Puan": round(puan, 2)
        })

    analiz_df = pd.DataFrame(analiz_listesi)
    analiz_df = analiz_df.sort_values(by="Toplam Puan", ascending=False)
    st.subheader(kosu_adi)
    st.dataframe(analiz_df, use_container_width=True)

if baslat and url:
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    kosular = soup.find_all("table")
    for idx, tablo in enumerate(kosular):
        th = tablo.find_previous("b")
        kosu_adi = th.text.strip() if th else f"{idx+1}. Koşu"

        rows = []
        trs = tablo.find_all("tr")[1:]
        headers = [th.text.strip() for th in tablo.find_all("tr")[0].find_all("td")]

        for tr in trs:
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue
            row = {headers[i]: tds[i].text.strip() for i in range(min(len(headers), len(tds)))}
            rows.append(row)

        if rows:
            analiz_tablosu(kosu_adi, rows)
