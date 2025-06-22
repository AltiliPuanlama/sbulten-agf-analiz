import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Trakus Excel Analizi", layout="wide")
st.title("🐎 Trakus Excel'den Yarış Analizi")

uploaded_file = st.file_uploader("📂 Trakus verisi içeren Excel dosyasını yükleyin (.xlsx)", type=["xlsx", "xls"])

def calculate_leader_bonus(df):
    at_adi_kolon = next((c for c in df.columns if "AD" in c.upper()), None)
    if not at_adi_kolon:
        return {}

    skor = {row[at_adi_kolon]: 0 for _, row in df.iterrows()}
    mesafe_kolonlari = [col for col in df.columns if re.match(r"\d{3,4}m", str(col))]

    for col in mesafe_kolonlari:
        sureler = pd.to_timedelta(df[col].astype(str).str.extract(r'(\d+:\d+\.\d+)')[0], errors='coerce')
        min_idx = sureler.idxmin()
        if pd.notna(min_idx):
            lider = df.loc[min_idx, at_adi_kolon]
            skor[lider] += 1

    return skor

def analiz_tablosu(kosu_adi, df):
    at_adi_kolon = next((c for c in df.columns if "AD" in c.upper()), None)
    if not at_adi_kolon:
        return pd.DataFrame()

    df["Ortalama Hız"] = pd.to_numeric(df.get("ORTALAMA HIZ", 0), errors="coerce").fillna(0)
    df["Maksimum Hız"] = pd.to_numeric(df.get("MAKSİMUM HIZ", 0), errors="coerce").fillna(0)

    liderlik = calculate_leader_bonus(df)
    df["Liderlik Skoru"] = df[at_adi_kolon].map(liderlik).fillna(0)

    df["Tempo Puanı"] = df["Ortalama Hız"] * 0.5 + df["Maksimum Hız"] * 0.3 + df["Liderlik Skoru"] * 1.5
    df = df.sort_values(by="Tempo Puanı", ascending=False)

    df = df[[at_adi_kolon, "Ortalama Hız", "Maksimum Hız", "Liderlik Skoru", "Tempo Puanı"]]
    df.columns = ["At Adı", "Ortalama Hız", "Maksimum Hız", "Liderlik Skoru", "Toplam Puan"]

    return df.reset_index(drop=True)

if uploaded_file:
    sheets = pd.read_excel(uploaded_file, sheet_name=None)
    for sheet, df in sheets.items():
        st.subheader(f"📊 {sheet}")
        analiz = analiz_tablosu(sheet, df)
        if analiz.empty:
            st.warning("Uygun veri bulunamadı.")
        else:
            st.dataframe(analiz, use_container_width=True)
