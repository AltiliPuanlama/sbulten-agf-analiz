
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://yenibeygir.com"

def temizle_para(deger):
    try:
        return float(deger.replace("₺", "").replace(".", "").replace(",", ".").strip())
    except:
        return 0.0

def parse_jokey_performans(link):
    jokey_dict, ant_dict, sahip_dict = {}, {}, {}
    try:
        r = requests.get(link)
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table tbody tr")
        for row in rows:
            cells = row.select("td")
            if len(cells) >= 12:
                jokey = cells[1].text.strip()
                jokey_dict[jokey] = cells[3].text.strip()
                ant_dict[jokey] = cells[7].text.strip()
                sahip_dict[jokey] = cells[11].text.strip()
    except:
        pass
    return jokey_dict, ant_dict, sahip_dict

def parse_stil(link):
    stil_dict = {}
    try:
        r = requests.get(link)
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table.StillerTable tbody tr")
        for row in rows:
            try:
                at_ismi = row.select_one("a.atisimlink").text.strip().lower()
                stil_kutulari = row.select("div.AtStyle > div[title*='%']")
                max_yuzde = -1
                baskin_index = -1
                for i, div in enumerate(stil_kutulari):
                    title = div.get("title", "")
                    if "%" in title:
                        yuzde = int(title.split("(")[-1].replace("%)", "").replace("%", ""))
                        if yuzde > max_yuzde:
                            max_yuzde = yuzde
                            baskin_index = i
                stil = "Bilinmiyor"
                if baskin_index == 0:
                    stil = "En Geride"
                elif baskin_index == 1:
                    stil = "Ortalarda"
                elif baskin_index == 2:
                    stil = "Öne Yakın"
                elif baskin_index == 3:
                    stil = "En Önde Kaçak"
                stil_dict[at_ismi] = stil
            except:
                continue
    except:
        pass
    return stil_dict

def parse_at_sayfasi(link):
    kum_kazanc = 0.0
    cim_kazanc = 0.0
    kilo_farki = 0.0
    try:
        r = requests.get(link)
        soup = BeautifulSoup(r.text, "html.parser")
        tablolar = soup.select("table")
        # Kazanç tablosu
        if len(tablolar) >= 1:
            rows = tablolar[0].select("tr")
            kazanc_index = next((i for i, th in enumerate(rows[0].select("th")) if "Kazanç" in th.text), -1)
            for row in rows[1:]:
                cells = row.select("td")
                if kazanc_index != -1 and len(cells) > kazanc_index:
                    pist = cells[0].text.strip()
                    kazanc = temizle_para(cells[kazanc_index].text)
                    if "Kum" in pist:
                        kum_kazanc = kazanc
                    elif "Çim" in pist:
                        cim_kazanc = kazanc
        # Kilo tablosu
        if len(tablolar) >= 2:
            rows = tablolar[1].select("tr")
            if len(rows) >= 3:
                bugun = float(rows[1].select("td")[7].text.replace(",", "."))
                onceki = float(rows[2].select("td")[7].text.replace(",", "."))
                kilo_farki = round(bugun - onceki, 2)
    except:
        pass
    return kum_kazanc, cim_kazanc, kilo_farki

def yarislari_cek(url):
    print(f"🔗 {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    yarislar = soup.select("div.yarisRow.Popup")
    kosular = {}

    for idx, yaris in enumerate(yarislar, 1):
        try:
            # Ek sayfa linklerini çek
            jokey_link = BASE_URL + yaris.select_one("a.yaris-jokeyperformans")["href"]
            stil_link = BASE_URL + yaris.select_one("a.yaris-stil")["href"]
            jokey_dict, ant_dict, sahip_dict = parse_jokey_performans(jokey_link)
            stil_dict = parse_stil(stil_link)
        except:
            jokey_dict, ant_dict, sahip_dict, stil_dict = {}, {}, {}, {}

        veriler = []
        rows = yaris.select("table.kosanAtlar tbody tr")
        for row in rows:
            try:
                at_no = row.select_one("td.atno").text.strip()
                at_link_tag = row.select_one("a.atisimlink")
                at_ismi = at_link_tag.text.strip()
                at_href = BASE_URL + at_link_tag["href"]
                yas = row.select("td")[3].text.strip()
                kilo = row.select_one("td.kilocell").text.strip()
                jokey = row.select("td")[5].text.strip()

                jokey_yuzde = jokey_dict.get(jokey, "Bilinmiyor")
                antrenor_yuzde = ant_dict.get(jokey, "Bilinmiyor")
                sahip_yuzde = sahip_dict.get(jokey, "Bilinmiyor")
                stil = stil_dict.get(at_ismi.lower(), "Bilinmiyor")
                kum_kazanc, cim_kazanc, kilo_farki = parse_at_sayfasi(at_href)

                veriler.append([
                    at_no, at_ismi, yas, kilo, jokey,
                    kum_kazanc, cim_kazanc, kilo_farki,
                    jokey_yuzde, antrenor_yuzde, sahip_yuzde, stil
                ])
                time.sleep(0.5)
            except:
                continue

        if veriler:
            df = pd.DataFrame(veriler, columns=[
                "At No", "At İsmi", "Yaş", "Kilo", "Jokey",
                "Kum Kazanç", "Çim Kazanç", "Kilo Farkı",
                "Jokey %", "Antrenör Başarı", "Sahip Başarı", "Atın Stili"
            ])
            kosular[idx] = df

    return kosular
