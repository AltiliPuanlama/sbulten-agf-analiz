# app.py

import streamlit as st
import pandas as pd
from analiz_modulu import get_tabs_for_city, get_yarislar_from_tab

st.set_page_config(layout="wide")
st.title("🏇 Sayısal Digital Bülten - Koşu Analiz Paneli")
st.markdown("---")

sehirler = {
    "Adana": "adana",
    "Ankara": "ankara",
    "Antalya": "antalya",
    "Bursa": "bursa",
    "Elazığ": "elazig",
    "İstanbul": "istanbul",
    "İzmir": "izmir",
    "Kocaeli": "kocaeli",
    "Şanlıurfa": "sanliurfa",
}

secilen_sehir = st.selectbox("📍 Lütfen analiz yapmak istediğiniz şehri seçin:", list(sehirler.keys()))

if secilen_sehir:
    city_slug = sehirler[secilen_sehir]
    tabs, city_url = get_tabs_for_city(city_slug)

    if not tabs:
        st.warning("Seçilen şehir için sayfada tab bulunamadı.")
    else:
        tab_labels = [t[0] for t in tabs]
        tab_indices = {t[0]: t[1] for t in tabs}

        secilen_tab = st.selectbox("🗂️ Lütfen analiz yapılacak TAB'ı seçin:", tab_labels)

        if secilen_tab and st.button("🚀 Analizi Başlat"):
            with st.spinner("Veriler analiz ediliyor, lütfen bekleyin..."):
                df_list = get_yarislar_from_tab(tab_indices[secilen_tab], city_url)

                if not df_list:
                    st.warning("Koşu verisi bulunamadı veya analiz sırasında hata oluştu.")
                else:
                    for i, df in enumerate(df_list):
                        st.subheader(f"🏁 {i+1}. Koşu")
                        st.dataframe(df, use_container_width=True)

            st.success("✅ Analiz tamamlandı!")
