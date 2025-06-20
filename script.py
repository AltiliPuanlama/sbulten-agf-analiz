import requests
from bs4 import BeautifulSoup
import pandas as pd

def yarislari_cek(url):
    print(f"🔗 Veri çekilecek adres: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print("Sayfa alınamadı.")
        return {}

    soup = BeautifulSoup(response.text, "html.parser")
    yarislar = soup.select("div.yarisRow.Popup")
    kosular = {}

    for i, yaris in enumerate(yarislar, 1):
        veriler = []
        satirlar = yaris.select("tr")

        for satir in satirlar:
            try:
                at_no = satir.select_one("td.atno").text.strip()
                at_ismi = satir.select_one("a.atisimlink").text.strip()
                yas = satir.select("td")[2].text.strip()
                kilo = satir.select_one("td.kilocell").text.strip()
                jokey = satir.select_one("a.bult-black").text.strip()

                # Dummy veriler ekliyoruz çünkü stil, kazanç, kilo farkı gibi bilgiler linklerden geliyordu (JS ile)
                kum_kazanc = 0
                cim_kazanc = 0
                kilo_farki = 0
                jokey_yuzde = 0
                antrenor_yuzde = 0
                sahip_yuzde = 0
                stil = "Bilinmiyor"

                veriler.append([
                    at_no, at_ismi, yas, kilo, jokey,
                    kum_kazanc, cim_kazanc, kilo_farki,
                    jokey_yuzde, antrenor_yuzde, sahip_yuzde, stil
                ])
            except:
                continue

        if veriler:
            df = pd.DataFrame(veriler, columns=[
                "At No", "At İsmi", "Yaş", "Kilo", "Jokey",
                "Kum Kazanç", "Çim Kazanç", "Kilo Farkı",
                "Jokey %", "Antrenör Başarı", "Sahip Başarı", "Atın Stili"
            ])
            kosular[i] = df

    return kosular
