import requests
from bs4 import BeautifulSoup
import pandas as pd

def yarislari_cek(url):
    print(f"🔗 Veriler çekiliyor: {url}")
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Yarış blokları
    yarislar = soup.select("div.yarisRow.Popup")
    kosular = {}

    for idx, yaris in enumerate(yarislar, 1):
        # Yarış başlığı
        baslik = yaris.select_one("h5.yarisBaslik").text.strip() if yaris.select_one("h5.yarisBaslik") else f"Yarış {idx}"
        
        veriler = []
        rows = yaris.select("tr")

        for satir in rows:
            cols = satir.select("td")
            if not cols or len(cols) < 5:
                continue
            
            try:
                at_no = cols[0].text.strip()
                at_ismi = cols[1].select_one("a.atisimlink").text.strip()
                yas = cols[2].text.strip()
                kilo = cols[3].text.strip()
                jokey = cols[4].select_one("a.bult-black").text.strip()

                # Ek sütunlar varsa al (örneğin kum, çim kazanç, kilo farkı sütunlarının sıra indisleri)
                kum_kazanc = cols[5].text.strip() if len(cols) > 5 else ""
                cim_kazanc = cols[6].text.strip() if len(cols) > 6 else ""
                kilo_fark = cols[7].text.strip() if len(cols) > 7 else ""
                jokey_yuzde = cols[8].text.strip() if len(cols) > 8 else ""
                antrenor_yuzde = cols[9].text.strip() if len(cols) > 9 else ""
                sahip_yuzde = cols[10].text.strip() if len(cols) > 10 else ""
                stil = cols[11].text.strip() if len(cols) > 11 else ""

                veriler.append([
                    at_no, at_ismi, yas, kilo, jokey,
                    kum_kazanc, cim_kazanc, kilo_fark,
                    jokey_yuzde, antrenor_yuzde, sahip_yuzde, stil
                ])
            except Exception as e:
                print(f"Satır atlandı: {e}")
                continue

        if veriler:
            df = pd.DataFrame(veriler, columns=[
                "At No", "At İsmi", "Yaş", "Kilo", "Jokey",
                "Kum Kazanç", "Çim Kazanç", "Kilo Farkı",
                "Jokey %", "Antrenör Başarı", "Sahip Başarı", "Stil"
            ])
            kosular[f"{idx}_{baslik}"] = df

    return kosular
