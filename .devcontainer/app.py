import streamlit as st
import pandas as pd

st.set_page_config(page_title="At Yarışı Trakus Analizi", layout="wide")
st.title("🐎 At Yarışı Trakus Analizi")

uploaded_file = st.file_uploader("Lütfen Trakus Excel dosyanızı yükleyin (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Excel dosyasını başlıksız olarak oku
        df_raw = pd.read_excel(uploaded_file, header=None)

        # Başlıklar 5. satır (index 4), veriler 6. satırdan itibaren (index 5+)
        df = df_raw.iloc[5:].copy()
        df.columns = df_raw.iloc[4]

        # "At ADI" sütunu aslında 2. sütun (index 1) → manuel çek
        df["At ADI"] = df.iloc[:, 1]

        # Mesafe sütunlarını yakala
        mesafe_cols = [col for col in df.columns if isinstance(col, str) and 'm' in col and '[' in str(df[col].iloc[0])]

        df["Eksik Mesafe Verisi"] = df[mesafe_cols].apply(lambda row: row.isin(["- [-]"]).sum(), axis=1)
        df["Geçerli Mesafe Sayısı"] = len(mesafe_cols) - df["Eksik Mesafe Verisi"]

        # Hızları sayıya çevir
        df["Maksimum Hız"] = pd.to_numeric(df.get("MAKSİMUM HIZ"), errors='coerce')
        df["Ortalama Hız"] = pd.to_numeric(df.get("ORTALAMA HIZ"), errors='coerce')

        # Sonuç tablosu
        analiz_df = df[["At ADI", "Maksimum Hız", "Ortalama Hız", "Eksik Mesafe Verisi", "Geçerli Mesafe Sayısı"]]

        st.success("✅ Analiz başarıyla tamamlandı")
        st.subheader("🏁 Sonuç Tablosu")
        st.dataframe(analiz_df.reset_index(drop=True))

    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
else:
    st.info("Lütfen analiz için bir Excel dosyası yükleyin.")
