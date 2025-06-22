import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Trakus Excel Analizi", layout="wide")
st.title("🐎 Trakus Excel'den Yarış Analizi")

uploaded_file = st.file_uploader("📂 Trakus verisi içeren Excel dosyasını yükleyin (.xlsx)", type=["xlsx", "xls"])

# Liderlik hesaplama
def calculate_leader_bonus(df):
    at_adi_kolon = next((c for c in df.columns if "AD" in c.upper()), None)
    if not at_adi_kolon:
        return {}

    liderlik_skoru = {row[at_adi_kolon]: 0 for _, row in df.iterrows()}
    mesafe_kolonlari = [col for col in df.columns if re.match(r"\d{3,4}m", str(col))]

    for col in mesafe_kolonlari:
        sureler = pd.to_timedelta(df[col].astype(str).str.extract(r'(\d+:\d+\.\d+)')[0], errors='coerce')
        min_idx = sureler.idxmin()
        if pd.notna(min_idx):
            lider_at = df.loc[min_idx, at_adi_kolon]
            liderlik_skoru[lider_at] += 1

    return liderlik_skoru

# Analiz
def analiz_tablosu(kosu_adi, df):
    at_adi_kolon = next((c for c in df.columns if "AD" in c.upper()), None)
    if not at_adi_kolon:
        return pd.DataFrame()

    df["Ortalama Hız"] = pd.to_numeric(df.get("ORTALAMA HIZ", 0), errors="coerce").fillna(0)
    df["Maksimum Hız"] = pd.to_numeric(df.get("MAKSİMUM HIZ", 0), errors="coerce").fillna(0)

    liderlik_bonus = calculate_leader_bonus(df)
    df["Liderlik Skoru"] = df[at_adi_kolon].map(liderlik_bonus).fillna(0)

    # Tempo puanı hesaplama (önem ağırlıklı)
    df["Tempo Puanı"] = df["Ortalama Hız"] * 0.5 + df["Maksimum Hız"] * 0.3 + df["Liderlik Skoru"] * 1.5
    df = df.sort_values(by="Tempo Puanı", ascending=False)

    df = df[[at_adi_kolon, "Ortalama Hız", "Maksimum Hız", "Liderlik Skoru", "Tempo Puanı"]]
    df.columns = ["At Adı", "Ortalama Hız", "Maksimum Hız", "Liderlik Skoru", "Toplam Puan"]

    return df.reset_index(drop=True)

# Ana analiz akışı
if uploaded_file:
    sheets = pd.read_excel(uploaded_file, sheet_name=None)

    for sheet_name, sheet_df in sheets.items():
        st.subheader(f"📊 {sheet_name}")
        if sheet_df.shape[0] < 2:
            st.info("Yeterli veri bulunamadı.")
            continue
        analiz_df = analiz_tablosu(sheet_name, sheet_df)
        if analiz_df.empty:
            st.warning("Analiz yapılamadı, uygun veri bulunamadı.")
        else:
            st.dataframe(analiz_df, use_container_width=True)
