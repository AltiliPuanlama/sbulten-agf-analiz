# app.py

import streamlit as st
import pandas as pd

st.set_page_config(page_title="At Yarışı Trakus Analizi", layout="wide")
st.title("🐎 At Yarışı Trakus Analizi")

uploaded_file = st.file_uploader("Lütfen Trakus Excel dosyanızı yükleyin (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Dosyayı ham olarak oku
        df_raw = pd.read_excel(uploaded_file, header=None)

        # Sütun başlıklarını 5. satırdan (index 4) al
        column_names = df_raw.iloc[4]
        df = df_raw.iloc[5:].copy()
        df.columns = column_names

        # Mesafe sütunlarını bul
        mesafe_cols = [col for col in df.columns if isinstance(col, str) and 'm' in col and '[' in str(df[col].iloc[0])]

        # Eksik geçiş verisi sayısı
        df["Eksik Mesafe Verisi"] = df[mesafe_cols].apply(lambda row: row.isin(["- [-]"]).sum(), axis=1)
        df["Geçerli Mesafe Sayısı"] = len(mesafe_cols) - df["Eksik Mesafe Verisi"]

        # Hızları sayıya çevir
        df["Maksimum Hız"] = pd.to_numeric(df["MAKSİMUM HIZ"], errors='coerce')
        df["Ortalama Hız"] = pd.to_numeric(df["ORTALAMA HIZ"], errors='coerce')

        # At adı sütunu varsa
        at_adi_kolonu = [col for col in df.columns if "At ADI" in str(col)]
        if not at_adi_kolonu:
            raise ValueError("Excel'de 'At ADI' sütunu bulunamadı.")

        # Sonuç tablosu
        analiz_df = df[[at_adi_kolonu[0], "Maksimum Hız", "Ortalama Hız", "Eksik Mesafe Verisi", "Geçerli Mesafe Sayısı"]]

        st.success("Analiz tamamlandı ✅")
        st.dataframe(analiz_df.reset_index(drop=True))

    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
else:
    st.info("Lütfen analiz için bir Excel dosyası yükleyin.")
