import streamlit as st
import pandas as pd

st.set_page_config(page_title="At Yarışı Trakus Analizi", layout="wide")
st.title("🐎 At Yarışı Trakus Analizi")

uploaded_file = st.file_uploader("Lütfen Trakus Excel dosyanızı yükleyin (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Excel dosyasını başlıksız olarak oku
        df_raw = pd.read_excel(uploaded_file, header=None)

        # Sütun başlıklarını 5. satırdan al (index 4)
        columns = df_raw.iloc[4]
        df = df_raw.iloc[5:].copy()
        df.columns = columns

        # 'At ADI' benzeri sütunu otomatik tespit et
        at_adi_col = None
        for col in df.columns:
            if isinstance(col, str) and "at" in col.lower() and "adi" in col.lower():
                at_adi_col = col
                break

        if at_adi_col is None:
            raise ValueError("'At ADI' benzeri bir sütun bulunamadı.")

        # Mesafe sütunlarını ayıkla (örneğin 200m, 400m...)
        mesafe_cols = [
            col for col in df.columns
            if isinstance(col, str) and 'm' in col and '[' in str(df[col].iloc[0])
        ]

        df["Eksik Mesafe Verisi"] = df[mesafe_cols].apply(lambda row: row.isin(["- [-]"]).sum(), axis=1)
        df["Geçerli Mesafe Sayısı"] = len(mesafe_cols) - df["Eksik Mesafe Verisi"]

        # Hızları sayıya çevir
        df["Maksimum Hız"] = pd.to_numeric(df.get("MAKSİMUM HIZ"), errors='coerce')
        df["Ortalama Hız"] = pd.to_numeric(df.get("ORTALAMA HIZ"), errors='coerce')

        # Sonuç tablosunu hazırla
        analiz_df = df[[at_adi_col, "Maksimum Hız", "Ortalama Hız", "Eksik Mesafe Verisi", "Geçerli Mesafe Sayısı"]]

        st.success("✅ Analiz başarıyla tamamlandı")
        st.subheader("🏁 Sonuç Tablosu")
        st.dataframe(analiz_df.reset_index(drop=True))

    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
else:
    st.info("Lütfen analiz için bir Excel dosyası yükleyin.")
