import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="Trakus Yarış Analiz", layout="wide")
st.title("🐎 Trakus Yarış Analiz Paneli")

# Kullanıcıdan tarih al
tarih_input = st.date_input("Tarih Seçiniz")
tarih = tarih_input.strftime("%Y%m%d")

# Şehir listesini çek
@st.cache_data(show_spinner=False)
def get_sehirler(tarih):
    url = f"http://91.151.93.198:5001/{tarih}"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    linkler = soup.select("div.navigator a")
    return [{"isim": a.text.strip(), "sehir": a['href'].split("/")[-1]} for a in linkler]

# Tempo analizine katkı sağlayan sütunlar
mesafe_sutunlari = [
    "200m", "400m", "600m", "800m", "1000m", "1200m",
    "1300m", "1400m", "1500m", "1600m", "1800m", "1900m",
    "2000m", "2100m", "2200m", "2400m"
]

def extract_seconds(value):
    """00:12.345 gibi string süreden saniyeye çevir"""
    try:
        match = re.search(r"(\d{2}):(\d{2}\.\d+)", value)
        if match:
            dakika = int(match.group(1))
            saniye = float(match.group(2))
            return dakika * 60 + saniye
    except:
        pass
    return None

def calculate_scores(df):
    df = df.copy()
    df["Tempo Skoru"] = 0
    liderlik_skoru = {row["AT ADI"]: 0 for _, row in df.iterrows()}

    # Her mesafe için en kısa sürede giden atı bul
    for mesafe in mesafe_sutunlari:
        if mesafe not in df.columns:
            continue
        sureler = df[mesafe].apply(extract_seconds)
        min_sure = sureler.min()
        for i, sure in enumerate(sureler):
            if sure is not None:
                tempo_puani = max(0, 100 - (sure - min_sure) * 10)
                df.at[i, "Tempo Skoru"] += tempo_puani
                if sure == min_sure:
                    at_adi = df.iloc[i]["AT ADI"]
                    liderlik_skoru[at_adi] += 10

    df["Maksimum Hız"] = pd.to_numeric(df.get("MAKSİMUM HIZ", 0), errors="coerce").fillna(0)
    df["Ortalama Hız"] = pd.to_numeric(df.get("ORTALAMA HIZ", 0), errors="coerce").fillna(0)
    df["Liderlik Skoru"] = df["AT ADI"].map(liderlik_skoru)
    
    df["Toplam Puan"] = (
        df["Tempo Skoru"] +
        df["Maksimum Hız"] * 2 +
        df["Ortalama Hız"] * 1.5 +
        df["Liderlik Skoru"]
    )

    df = df.sort_values("Toplam Puan", ascending=False)
    return df

# Koşuları analiz et
def analyze_sehir(tarih, sehir):
    url = f"http://91.151.93.198:5001/{tarih}/{sehir}"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    tablolar = soup.find_all("table")
    basliklar = soup.find_all(string=re.compile(r"Koşu "))
    analizler = []

    for i, tablo in enumerate(tablolar):
        try:
            headers = [th.text.strip().upper() for th in tablo.find_all("th")]
            rows = []
            for tr in tablo.find_all("tr"):
                tds = tr.find_all("td")
                if not tds:
                    continue
                row = {headers[i]: tds[i].text.strip() for i in range(min(len(headers), len(tds)))}
                rows.append(row)

            if len(rows) == 0:
                continue
            df = pd.DataFrame(rows)
            df.columns = [c.upper() for c in df.columns]
            df = calculate_scores(df)
            baslik = basliklar[i].strip() if i < len(basliklar) else f"Koşu {i+1}"
            analizler.append((baslik, df))
        except Exception:
            continue

    return analizler

# Şehirleri getir ve seçtirme
sehirler = get_sehirler(tarih)
sehir_adi = st.selectbox("Şehir Seçiniz", [s['isim'] for s in sehirler])

if st.button("Analizi Başlat"):
    with st.spinner("Veriler getiriliyor..."):
        analizler = analyze_sehir(tarih, sehir_adi)

    if not analizler:
        st.warning("Bu şehir için analiz bulunamadı.")
    else:
        for baslik, df in analizler:
            st.markdown(f"### 📊 {baslik} - Trakus Analiz Tablosu")
            st.dataframe(df[["AT ADI", "Tempo Skoru", "Maksimum Hız", "Ortalama Hız", "Liderlik Skoru", "Toplam Puan"]], use_container_width=True)
