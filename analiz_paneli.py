import streamlit as st
import pandas as pd
import requests
from datetime import date

st.set_page_config(page_title="Yarış Analiz Paneli", layout="wide")
st.title("🏇 Yarış Analiz Paneli")

# 📅 Tarih ve şehir seçimi
secilen_tarih = st.date_input("Tarih Seçiniz", value=date.today())
sehirler = ["istanbul", "ankara", "izmir", "adana", "bursa", "kocaeli", "urfa", "elazig"]
secilen_sehir = st.selectbox("Şehir Seçiniz", options=sehirler)

# 🔗 API linki oluştur
tarih_str = secilen_tarih.strftime("%d-%m-%Y")
api_url = f"http://www.yenibeygir.com/{tarih_str}/{secilen_sehir}"
st.markdown(f"🔗 **Veri çekilecek API:** `{api_url}`")

# Başlat
if st.button("🔍 Analizi Başlat"):
    with st.spinner("Veriler API'den çekiliyor..."):
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            kosular_json = response.json()
        except Exception as e:
            st.error(f"Veri çekme hatası: {e}")
            st.stop()

    def puan_hesapla(row):
        puan = 0
        try:
            puan += float(str(row["Jokey %"]).replace(",", ".")) * 1.5
            puan += float(str(row["Antrenör Başarı"]).replace(",", ".")) * 1.2
            puan += float(str(row["Sahip Başarı"]).replace(",", ".")) * 1.0
        except:
            pass
        try:
            puan += float(row["Kum Kazanç"]) * 0.0005
            puan += float(row["Çim Kazanç"]) * 0.0005
        except:
            pass
        if row["Atın Stili"] == "En Önde Kaçak":
            puan += 3
        elif row["Atın Stili"] == "Öne Yakın":
            puan += 2
        elif row["Atın Stili"] == "Ortalarda":
            puan += 1
        try:
            kilo_fark = float(row["Kilo Farkı"])
            puan -= abs(kilo_fark) * 0.5
        except:
            pass
        return round(puan, 2)

    # 🌟 En Şanslı Atlar
    st.subheader("🌟 En Şanslı Atlar")
    favoriler = []
    for kosu_no, satirlar in kosular_json.items():
        df = pd.DataFrame(satirlar)
        df["Puan"] = df.apply(puan_hesapla, axis=1)
        en_iyi = df.sort_values("Puan", ascending=False).head(1)
        en_iyi.insert(0, "Koşu No", kosu_no)
        favoriler.append(en_iyi)

    favori_df = pd.concat(favoriler)
    gosterilecek = [c for c in favori_df.columns if c not in ["Yaş", "Kilo Farkı"]]
    st.dataframe(favori_df[gosterilecek].reset_index(drop=True), use_container_width=True)

    # 📄 Tüm Koşular
    st.subheader("📄 Tüm Koşular")
    for kosu_no, satirlar in kosular_json.items():
        df = pd.DataFrame(satirlar)
        df["Puan"] = df.apply(puan_hesapla, axis=1)
        st.markdown(f"### {kosu_no}. Koşu")
        gosterilecek = [c for c in df.columns if c not in ["Yaş", "Kilo Farkı"]]
        st.dataframe(df[gosterilecek].reset_index(drop=True), use_container_width=True)
