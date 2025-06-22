import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="Trakus Verileri Analiz Paneli", layout="wide")
st.title("🐎 Trakus Verileri Analiz Paneli")

# Kullanıcıdan tam URL alın
default_url = "http://91.151.93.198:5001/20250622/ADANA"
url_input = st.text_input("Trakus Sayfası URL'si", value=default_url)

# Süreyi saniyeye çevir
def extract_seconds(value):
    try:
        match = re.search(r"(\d{2}):(\d{2}\.\d+)", value)
        if match:
            dakika = int(match.group(1))
            saniye = float(match.group(2))
            return dakika * 60 + saniye
    except:
        pass
    return None

# Tempo analizini yap
def calculate_scores(df):
    df = df.copy()
    mesafeler = [col for col in df.columns if re.match(r"\d{3,4}m", col)]
    
    # AT ADI sütunu bulma
    at_adi_kolon = next((c for c in df.columns if "AT" in c and "AD" in c), None)
    if not at_adi_kolon:
        return None

    df["Tempo Skoru"] = 0
    df["Liderlik Skoru"] = 0

    for mesafe in mesafeler:
        sureler = df[mesafe].apply(extract_seconds)
        min_sure = sureler.min()
        for i, sure in enumerate(sureler):
            if pd.notnull(sure) and pd.notnull(min_sure):
                tempo = max(0, 100 - (sure - min_sure) * 10)
                df.at[i, "Tempo Skoru"] += tempo
                if sure == min_sure:
                    df.at[i, "Liderlik Skoru"] += 10

    df["Maksimum Hız"] = pd.to_numeric(df.get("MAKSİMUM HIZ", 0), errors="coerce").fillna(0)
    df["Ortalama Hız"] = pd.to_numeric(df.get("ORTALAMA HIZ", 0), errors="coerce").fillna(0)

    df["Toplam Puan"] = (
        df["Tempo Skoru"] +
        df["Maksimum Hız"] * 2 +
        df["Ortalama Hız"] * 1.5 +
        df["Liderlik Skoru"]
    )

    df = df.sort_values("Toplam Puan", ascending=False)

    return df[[at_adi_kolon, "Tempo Skoru", "Liderlik Skoru", "Maksimum Hız", "Ortalama Hız", "Toplam Puan"]]

# Sayfadaki tabloları al
def analiz_et(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    tablolar = soup.find_all("table")
    basliklar = soup.find_all(string=re.compile(r"Koşu "))

    analizler = []

    for i, tablo in enumerate(tablolar):
        try:
            df = pd.read_html(str(tablo))[0]
            if df.empty or df.shape[1] < 5:
                continue
            skor_df = calculate_scores(df)
            if skor_df is not None:
                baslik = basliklar[i].strip() if i < len(basliklar) else f"Koşu {i+1}"
                analizler.append((baslik, skor_df))
        except Exception:
            continue
    return analizler

if st.button("Analiz Et"):
    with st.spinner("Analiz yapılıyor..."):
        try:
            analizler = analiz_et(url_input)
            if not analizler:
                st.warning("Hiç analiz yapılacak tablo bulunamadı.")
            else:
                for baslik, skor_df in analizler:
                    st.subheader(f"📊 {baslik} - Trakus Analiz")
                    st.dataframe(skor_df, use_container_width=True)
        except Exception as e:
            st.error(f"Hata oluştu: {str(e)}")
