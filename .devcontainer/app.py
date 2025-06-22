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

# Seçilen şehrin koşularını analiz et
def analyze_sehir(tarih, sehir):
    url = f"http://91.151.93.198:5001/{tarih}/{sehir}"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    tablolar = soup.find_all("table")
    basliklar = soup.find_all(string=re.compile(r"Koşu "))
    analizler = []

    for i, tablo in enumerate(tablolar):
        try:
            df = pd.read_html(str(tablo))[0]
            df.columns = [str(c) for c in df.columns]  # 👈 TypeError çözümü
            if df.empty or df.shape[1] < 5:
                continue
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
            st.subheader(baslik)
            st.dataframe(df, use_container_width=True)
