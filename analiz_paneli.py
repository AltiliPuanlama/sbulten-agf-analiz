import streamlit as st
import pandas as pd
import script  # script.py ile aynı klasörde olmalı
from datetime import date

st.set_page_config(page_title="Yarış Analiz Paneli", layout="wide")
st.title("🏇 SAYISAL DİGİTAL BÜLTEN Kullanıcı ÖZEL Analiz Paneli")

# 📅 Tarih seçimi
secilen_tarih = st.date_input("Tarih Seçiniz", value=date.today())

# 🏙️ Şehir seçimi
sehirler = ["istanbul", "ankara", "izmir", "adana", "bursa", "kocaeli", "sanliurfa", "elazig", "diyarbakir"]
secilen_sehir = st.selectbox("Şehir Seçiniz", options=sehirler)

# 🔗 Link oluştur
tarih_str = secilen_tarih.strftime("%d-%m-%Y")
url = f"https://yenibeygir.com/{tarih_str}/{secilen_sehir}"


# 🚀 Analizi Başlat
if st.button("🔍 Analizi Başlat"):
    with st.spinner("Veriler çekiliyor... SAYISAL DİGİTAL BÜLTEN"):
                kosular = script.yarislari_cek(url)

    if not kosular:
        st.warning("Seçilen sayfada yarış bulunamadı.")
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
    for kosu_no, df in kosular.items():
        df["Puan"] = df.apply(puan_hesapla, axis=1)
        en_iyi = df.sort_values("Puan", ascending=False).head(1)
        en_iyi.insert(0, "Koşu No", kosu_no)
        favoriler.append(en_iyi)
    favori_df = pd.concat(favoriler)
    st.dataframe(favori_df.reset_index(drop=True), use_container_width=True)

    # 📄 Tüm Koşular
    st.subheader("📄 Tüm Koşular")
    for kosu_no, df in kosular.items():
        df["Puan"] = df.apply(puan_hesapla, axis=1)
        st.markdown(f"### {kosu_no}. Koşu")
        st.dataframe(df.reset_index(drop=True), use_container_width=True)

else:
    st.info("Tarih ve şehir seçip ardından 'Analizi Başlat' butonuna tıklayın.")
