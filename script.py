
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://yenibeygir.com"

def parse_yarislar(soup):
    kosular = {}
    yarislar = soup.select("div.yarisRow.Popup")
    for idx, yaris in enumerate(yarislar, 1):
        veriler = []
        rows = yaris.select("table.kosanAtlar tbody tr")
        for row in rows:
            try:
                agf = row.select("td")[0].text.strip()
                at_no = row.select_one("td.atno").text.strip()
                at_ismi = row.select_one("a.atisimlink").text.strip()
                yas = row.select("td")[3].text.strip()
                kilo = row.select_one("td.kilocell").text.strip()
                jokey = row.select("td")[5].text.strip()
                sahip = row.select("td")[7].text.strip()
                kulvar = row.select("td")[8].text.strip()
                son10 = " ".join(row.select("td")[9].stripped_strings)
                hnd = row.select("td")[10].text.strip()
                gs20 = " ".join(x.text.strip() for x in row.select("td")[11].select("span"))
                sonuc = row.select("td")[12].text.strip()

                # === Ayrı sayfalardan alınanlar (şimdilik dummy) ===
                jokey_yuzde = "Bilinmiyor"
                antrenor_yuzde = "Bilinmiyor"
                sahip_yuzde = "Bilinmiyor"
                stil = "Bilinmiyor"
                kum_kazanc = 0
                cim_kazanc = 0
                kilo_farki = 0

                veriler.append([
                    at_no, at_ismi, yas, kilo, jokey, sahip,
                    agf, kulvar, son10, hnd, gs20, sonuc,
                    jokey_yuzde, antrenor_yuzde, sahip_yuzde,
                    stil, kum_kazanc, cim_kazanc, kilo_farki
                ])
            except Exception as e:
                continue

        if veriler:
            df = pd.DataFrame(veriler, columns=[
                "At No", "At İsmi", "Yaş", "Kilo", "Jokey", "Sahip/Ant",
                "AGF", "Kulvar", "Son 10", "Handikap", "G/S20", "Sonuç",
                "Jokey %", "Antrenör Başarı", "Sahip Başarı",
                "Atın Stili", "Kum Kazanç", "Çim Kazanç", "Kilo Farkı"
            ])
            kosular[idx] = df
    return kosular

def yarislari_cek(url):
    print(f"🔗 Veriler çekiliyor: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Sayfa alınamadı.")
        return {}
    soup = BeautifulSoup(response.text, "html.parser")
    return parse_yarislar(soup)
