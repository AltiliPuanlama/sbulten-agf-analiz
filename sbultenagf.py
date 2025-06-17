import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# ⚡️ Otomatik yenileme (5 dakika)
st_autorefresh(interval=5 * 60 * 1000, key="auto_refresh")

# ✨ Sayfa ayarı
st.set_page_config(page_title="Sayısal Bülten AGF Takip", layout="centered")
st.title("\ud83c\udfcf AGF Takip ve Analiz Web Paneli")

# ⏰ Saat bilgisi
def turkiye_saati():
    return datetime.now(pytz.timezone("Europe/Istanbul"))

# 🔹 Kullanıcı girişleri
agf_url = st.text_input("TJK AGF Sayfası Linki", " ")
saat_input = st.text_input("Veri çekim saatlerini girin (14:00,15:30 vb.)", " ")
cek_buton = st.button("\ud83d\udd0d Verileri Çek ve Analiz Et")

status_text = st.empty()

# 📂 Bellek içi veri saklama
if "veriler" not in st.session_state:
    st.session_state.veriler = []
if "cekilen_saatler" not in st.session_state:
    st.session_state.cekilen_saatler = []
if "hedef_saatler" not in st.session_state:
    st.session_state.hedef_saatler = []

# 🔍 AGF veri çekme fonksiyonu
def fetch_agf():
    now = turkiye_saati()
    timestamp = now.strftime("%H:%M")
    status_text.info(f"\u23f3 [{timestamp}] Veri çekiliyor...")
    try:
        response = requests.get(agf_url)
        soup = BeautifulSoup(response.content, "html.parser")
        for ayak in range(1, 7):
            table = soup.find("table", {"id": f"GridView{ayak}"})
            if not table:
                continue
            rows = table.find_all("tr")[1:]
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    cell_text = cells[1].text.strip()
                    if "(" in cell_text and "%" in cell_text:
                        at_no = cell_text.split("(")[0].strip()
                        agf_percent = cell_text.split("%")[-1].replace(")", "").replace(",", ".")
                        st.session_state.veriler.append({
                            "Saat": timestamp,
                            "Ayak": ayak,
                            "At": at_no,
                            "AGF": float(agf_percent)
                        })
        status_text.success(f"\u2705 [{timestamp}] Veri çekildi.")
    except Exception as e:
        status_text.error(f"\u26a0\ufe0f Hata: {e}")

# 🔢 Analiz fonksiyonu
def analiz_ve_goster():
    veri_df = pd.DataFrame(st.session_state.veriler)
    if veri_df.empty:
        st.warning("Henüz yeterli veri yok.")
        return
    for ayak in sorted(veri_df["Ayak"].unique()):
        df = veri_df[veri_df["Ayak"] == ayak][["Saat", "At", "AGF"]]
        pivot_df = df.pivot(index="At", columns="Saat", values="AGF").reset_index()
        pivot_df = pivot_df.dropna(how="all", axis=1)
        if pivot_df.shape[1] < 3:
            continue

        saatler = pivot_df.columns[1:]
        pivot_df["Toplam AGF Değişimi"] = pivot_df[saatler[-1]] - pivot_df[saatler[0]]
        pivot_df["Standart Sapma"] = pivot_df[saatler].std(axis=1)

        st.subheader(f"\ud83d\udcca {ayak}. Ayak")
        st.dataframe(pivot_df, use_container_width=True)

# ✅ Saat kontrolü
if cek_buton:
    st.session_state.hedef_saatler = [s.strip() for s in saat_input.split(",") if s.strip()]

simdi = turkiye_saati().strftime("%H:%M")
for hedef_saat in st.session_state.hedef_saatler:
    if simdi == hedef_saat and hedef_saat not in st.session_state.cekilen_saatler:
        fetch_agf()
        st.session_state.cekilen_saatler.append(hedef_saat)

# ✨ Mevcut veri varsa analiz et
df_check = pd.DataFrame(st.session_state.veriler)
if not df_check.empty:
    analiz_ve_goster()

if all(s in st.session_state.cekilen_saatler for s in st.session_state.hedef_saatler):
    status_text.success("\u2705 Tüm veriler başarıyla alındı. SAYISAL DİGİTAL BÜLTEN farkıyla!")
