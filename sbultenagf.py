import streamlit as st
import pandas as pd
import numpy as np
import requests
import sys
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import pytz  # Türkiye saati icin
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_autorefresh import st_autorefresh

# 📌 Streamlit sayfa ayarları (ilk komut olmalı)
st.set_page_config(page_title="Sayısal Digital Bülten AGF Takip Paneli", layout="centered")

# Google Sheets Ayarları
SHEET_ID = "14Uc1bQ6nhA4dBF7c4W4XDsmHOOCwJfFb_IZnLmp03gc"
SHEET_NAME = "Sayfa1"

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# Otomatik yenileme (5 dakika)
st_autorefresh(interval=5 * 60 * 1000, key="otomatik_yenileme")

st.title("🏏 AGF Takip ve Analiz Web Paneli")

st.markdown("### TJK AGF Sayfası Linki")
agf_url = st.text_input("TJK AGF Sayfası Linki", " ")

saat_input = st.text_input("Veri çekim saatlerini girin (örn: 14:00,15:15,16:30)", " ")
cek_buton = st.button("🔍 Verileri Çek ve Analiz Et")

progress_bar = st.empty()
status_text = st.empty()
sonuc_alan = st.empty()

def turkiye_saati():
    return datetime.now(pytz.timezone("Europe/Istanbul"))

@st.cache_data(show_spinner=False)
def load_data_from_sheet():
    try:
        rows = sheet.get_all_records()
        df = pd.DataFrame(rows)
        return df
    except:
        return pd.DataFrame(columns=["Saat", "Ayak", "At", "AGF"])

agf_raw_df = load_data_from_sheet()
agf_data_dict = {}
if "cekilen_saatler" not in st.session_state:
    st.session_state.cekilen_saatler = []
if "hedef_saatler" not in st.session_state:
    st.session_state.hedef_saatler = []

def saat_eslesiyor_mu(simdi, hedef_saat):
    simdi_dt = datetime.strptime(simdi, "%H:%M")
    hedef_dt = datetime.strptime(hedef_saat, "%H:%M")
    fark = abs((simdi_dt - hedef_dt).total_seconds()) / 60
    return fark <= 1  # 1 dakika tolerans

# --- Yardımcı Fonksiyonlar ---
def belirle_surpriz_tipi(row, saatler):
    try:
        agf_values = row[1:-1].dropna().astype(float)
        if len(agf_values) < 3:
            return ""

        ilk_agf = agf_values.iloc[0]
        son_agf = agf_values.iloc[-1]
        fark_ilk_son = son_agf - ilk_agf

        if son_agf < 10 and fark_ilk_son >= 1.0:
            return f"ÇÜrpriz (%+{fark_ilk_son:.1f})"

        if len(saatler) >= 2 and saatler[-1] != saatler[0]:
            son_saat = saatler[-1]
            onceki_saat = saatler[-2]
            son1 = row[son_saat]
            son2 = row[onceki_saat]
            if pd.notna(son1) and pd.notna(son2):
                fark_son_dk = float(son1) - float(son2)
                if fark_son_dk >= 0.3 and float(son1) < 10:
                    return f"Son DK Sürpriz (%+{fark_son_dk:.1f})"
    except:
        return ""
    return ""

def fetch_agf():
    now = turkiye_saati()
    timestamp = now.strftime("%H:%M")
    status_text.info(f"⏳ [{timestamp}] AGF verisi çekiliyor...")

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
                        agf_percent = cell_text.split("%")[1].replace(")", "").replace(",", ".")
                        sheet.append_row([timestamp, ayak, at_no, float(agf_percent)])

        status_text.success(f"✅ [{timestamp}] Veri çekildi.")
    except Exception as e:
        status_text.error(f"⚠️ Hata: {e}")

def analiz_ve_goster():
    agf_data_dict.clear()
    for ayak in range(1, 7):
        df = agf_raw_df[agf_raw_df["Ayak"] == ayak][["Saat", "At", "AGF"]]
        pivot_df = df.pivot(index="At", columns="Saat", values="AGF").reset_index()
        pivot_df = pivot_df.dropna(how="all", axis=1)
        if pivot_df.shape[1] < 3:
            st.warning(f"{ayak}. ayakta yeterli veri yok.")
            continue

        saatler = pivot_df.columns[1:].tolist()
        last_col = pivot_df.columns[-1]
        pivot_df["Toplam AGF Değişim %"] = pivot_df[last_col] - pivot_df[pivot_df.columns[1]]
        pivot_df["Sabit Çok Değişmeyen AGFLER"] = pivot_df[pivot_df.columns[1:-1]].std(axis=1)
        pivot_df["Sürekli Artış Göstermiş Atlar"] = pivot_df[pivot_df.columns[1:-1]].diff(axis=1).apply(lambda x: sum([1 if v > 0 else -1 if v < 0 else 0 for v in x.dropna()]), axis=1)
        pivot_df["Sürpriz Tipi"] = pivot_df.apply(lambda row: belirle_surpriz_tipi(row, saatler), axis=1)

        max_values = {
            "Sürekli Artış Göstermiş Atlar": pivot_df["Sürekli Artış Göstermiş Atlar"].max(),
            "Toplam AGF Değişim %": pivot_df["Toplam AGF Değişim %"].max(),
            "Sabit Çok Değişmeyen AGFLER": pivot_df["Sabit Çok Değişmeyen AGFLER"].max()
        }

        def highlight(val, col):
            try:
                if pd.isna(val): return ""
                if val == max_values[col]:
                    return "background-color: lightgreen"
                if col == "Toplam AGF Değişim %" and val >= 0.74:
                    return "background-color: orange"
                if col in ["Sürekli Artış Göstermiş Atlar", "Sabit Çok Değişmeyen AGFLER"]:
                    top3 = pivot_df[col].sort_values(ascending=False).drop_duplicates().nlargest(4)[1:]
                    if val in top3.values:
                        return "background-color: orange"
            except:
                return ""
            return ""

        gosterilecek_sutunlar = ["At", "Toplam AGF Değişim %", "Sabit Çok Değişmeyen AGFLER", "Sürekli Artış Göstermiş Atlar", "Sürpriz Tipi"]
        df_gosterim = pivot_df[gosterilecek_sutunlar]

        styled_df = df_gosterim.style\
            .applymap(lambda v: highlight(v, "Sürekli Artış Göstermiş Atlar"), subset=["Sürekli Artış Göstermiş Atlar"])\
            .applymap(lambda v: highlight(v, "Toplam AGF Değişim %"), subset=["Toplam AGF Değişim %"])\
            .applymap(lambda v: highlight(v, "Sabit Çok Değişmeyen AGFLER"), subset=["Sabit Çok Değişmeyen AGFLER"])

        st.subheader(f"📊 {ayak}. Ayak Analizi")
        try:
            st.dataframe(styled_df, use_container_width=True)
        except:
            st.write(df_gosterim)

if cek_buton:
    st.session_state.hedef_saatler = [s.strip() for s in saat_input.split(",") if s.strip()]

simdi = turkiye_saati().strftime("%H:%M")
for hedef_saat in st.session_state.hedef_saatler:
    if saat_eslesiyor_mu(simdi, hedef_saat) and hedef_saat not in st.session_state.cekilen_saatler:
        fetch_agf()
        agf_raw_df = load_data_from_sheet()
        analiz_ve_goster()
        st.session_state.cekilen_saatler.append(hedef_saat)

if not agf_raw_df.empty:
    analiz_ve_goster()

if all(saat in st.session_state.cekilen_saatler for saat in st.session_state.hedef_saatler):
    status_text.success("✅ Tüm veriler başarıyla çekildi. SAYISAL DİGİTAL BÜLTEN FARKI İLE...")
