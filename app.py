# app.py
import streamlit as st
import pandas as pd
from analiz_modulu import get_tabs, get_yarislar_from_tab, analiz_et, orijin_analizi

st.set_page_config(layout="wide")
st.title("🏇 Sayısal Digital Bülten - At Yarışı Analiz Paneli")
st.markdown("---")

# Tabs (şehir sekmeleri) çekiliyor
with st.spinner("📡 Sekmeler yükleniyor..."):
    try:
        tabs = get_tabs()
    except Exception as e:
        st.error(f"❌ Sekmeler alınamadı: {e}")
        st.stop()

tab_names = [isim for isim, _ in tabs]
secili_tab = st.selectbox("📍 Hangi şehir/sekme analiz edilsin?", tab_names)

if st.button("🚀 Analizi Başlat"):
    secilen_index = dict(tabs)[secili_tab]

    with st.spinner("🔎 Yarış verileri toplanıyor..."):
        df_list = get_yarislar_from_tab(secilen_index)

    if not df_list:
        st.warning("⚠️ Bu sekmede analiz edilecek veri bulunamadı.")
        st.stop()

    # En şanslı atlar
    sansli_df = analiz_et(df_list)

    # Orijin analizi (aynı babadan gelen atlar)
    orijin_df = orijin_analizi(df_list)

    st.success("✅ Tüm analiz tamamlandı!")

    # En şanslı atlar
    st.subheader("🥇 En Şanslı Atlar (Her Koşudan)")
    sansli_df_show = sansli_df.drop(columns=["Koşu No", "Baba", "Anne", "Anne Baba"], errors='ignore')
    sansli_df_show["Puan"] = sansli_df["Puan"].apply(lambda x: f"**:red[{x}]**" if x == sansli_df["Puan"].max() else str(x))
    st.dataframe(sansli_df_show.reset_index(drop=True), use_container_width=True)

    # Orijin analizi
    st.subheader("🧬 Orijin Analizi (En çok at veren babalar)")
    st.dataframe(orijin_df.reset_index(drop=True), use_container_width=True)

    # Tüm detaylar
    with st.expander("📊 Tüm Koşu Verileri"):
        for i, df in enumerate(df_list):
            st.markdown(f"### {i+1}. Koşu")
            df_show = df.drop(columns=["Koşu No", "Baba", "Anne", "Anne Baba"], errors='ignore')
            st.dataframe(df_show.reset_index(drop=True), use_container_width=True)
