# app.py

import streamlit as st
import pandas as pd

st.set_page_config(page_title="At Yarışı Trakus Analizi", layout="wide")
st.title("🐎 At Yarışı Trakus Analizi")

uploaded_file = st.file_uploader("Lütfen Trakus Excel dosyanızı yükleyin (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Excel dosyasını oku
        df = pd.read_excel(uploaded_file)

        # Veri ve başlık ayrımı (temizlemeden)
        veri_df = df.iloc[4:].copy()
        veri_df.columns = df.iloc[3]

        # Mesafe sütunlarını yakala (örnek: 200m, 400m...)
        mesafe_sutunlari = [
            col for col in veri_df.columns
            if isinstance(col, str) and "m" in col and "[" in str(veri_df[col].iloc[0])
        ]

        # Eksik/verili geçiş sayısı hesapla
        veri_df["Eksik Mesafe Verisi"] = veri_df[mesafe_sutunlari].apply(
            lambda row: row.isin(["- [-]"]).sum(), axis=1
        )
        veri_df["Geçerli Mesafe Sayısı"] = len(mesafe_sutunlari) - veri_df["Eksik Mesafe Verisi"]

        # Hız verilerini sayısal hale getir
        veri_df["Maksimum Hız"] = pd.to_numeric(veri_df["MAKSİMUM HIZ"], errors='coerce')
        veri_df["Ortalama Hız"] = pd.to_numeric(veri_df["ORTALAMA HIZ"], errors='coerce')

        # Sadece analiz için gerekli sütunları al
        analiz_df = veri_df[
            ["At ADI", "Maksimum Hız", "Ortalama Hız", "Eksik Mesafe Verisi", "Geçerli Mesafe Sayısı"]
        ]

        st.success("Analiz başarıyla tamamlandı!")
        st.subheader("🏁 At Bazlı Trakus Analiz Sonuçları")
        st.dataframe(analiz_df.reset_index(drop=True))

    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")

else:
    st.info("Lütfen analiz için bir Excel dosyası yükleyin.")
