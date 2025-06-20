# analiz_modulu.py (güncellendi: stil verisi düzeltildi + gerçekçi en şanslı at seçimi)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import re

def _get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_tabs():
    driver = _get_driver()
    driver.get("https://yenibeygir.com/")
    time.sleep(3)
    tabs = driver.find_elements(By.CSS_SELECTOR, "ul.BultenTabs li")
    tab_list = [(tab.text.strip(), i) for i, tab in enumerate(tabs) if tab.text.strip()]
    driver.quit()
    return tab_list

def get_yarislar_from_tab(tab_index):
    driver = _get_driver()
    driver.get("https://yenibeygir.com/")
    time.sleep(3)
    tabs = driver.find_elements(By.CSS_SELECTOR, "ul.BultenTabs li")
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(tabs[tab_index]))
    driver.execute_script("arguments[0].scrollIntoView(true);", tabs[tab_index])
    driver.execute_script("arguments[0].click();", tabs[tab_index])
    time.sleep(3)

    yarislar = driver.find_elements(By.CSS_SELECTOR, "div.yarisRow.Popup")
    df_list = []

    for i, yaris in enumerate(yarislar):
        try:
            saat = yaris.find_element(By.CSS_SELECTOR, ".yarisSaat span").text
            grup = yaris.find_element(By.CSS_SELECTOR, ".yarisGrup span").text
            try:
                pist_mesafe = yaris.find_element(By.CSS_SELECTOR, ".kumpist").text
            except:
                try:
                    pist_mesafe = yaris.find_element(By.CSS_SELECTOR, ".cimpist").text
                except:
                    pist_mesafe = "Bilinmiyor"

            jokey_perf_dict = {}
            antrenor_perf_dict = {}
            sahip_perf_dict = {}
            try:
                jokey_link = yaris.find_element(By.CSS_SELECTOR, "a.yaris-jokeyperformans").get_attribute("href")
                driver.execute_script("window.open(arguments[0]);", jokey_link)
                driver.switch_to.window(driver.window_handles[1])
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr")))
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 11:
                        jokey_adi = cells[1].text.strip()
                        jokey_perf_dict[jokey_adi] = cells[3].text.strip()
                        antrenor_perf_dict[jokey_adi] = cells[7].text.strip()
                        sahip_perf_dict[jokey_adi] = cells[11].text.strip()
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except:
                pass

            # Stil verisi düzeltildi
            stil_dict = {}
            try:
                stil_link = yaris.find_element(By.CSS_SELECTOR, "a.yaris-stil").get_attribute("href")
                driver.execute_script("window.open(arguments[0]);", stil_link)
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(2)
                rows = driver.find_elements(By.CSS_SELECTOR, "table.StillerTable tbody tr")
                for row in rows:
                    try:
                        at_ismi = row.find_element(By.CSS_SELECTOR, "a.atisimlink").text.strip()
                        kutular = row.find_elements(By.CSS_SELECTOR, "div.AtStyle > div[title*='%']")
                        max_yuzde = -1
                        index = -1
                        for i, k in enumerate(kutular):
                            title = k.get_attribute("title")
                            if '%' in title:
                                try:
                                    yuzde = int(re.findall(r"%([0-9]+)", title)[0])
                                    if yuzde > max_yuzde:
                                        max_yuzde = yuzde
                                        index = i
                                except:
                                    continue
                        stil = "Bilinmiyor"
                        if index == 0: stil = "En Geride"
                        elif index == 1: stil = "Ortalarda"
                        elif index == 2: stil = "Öne Yakın"
                        elif index == 3: stil = "En Önde Kaçak"
                        stil_dict[at_ismi.lower()] = stil
                    except:
                        continue
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except:
                stil_dict = {}

            veriler = []
            atlar = yaris.find_elements(By.CSS_SELECTOR, "tr")
            for satir in atlar:
                try:
                    at_no = satir.find_element(By.CSS_SELECTOR, "td.atno").text
                    at_ismi_tag = satir.find_element(By.CSS_SELECTOR, "a.atisimlink")
                    at_ismi = at_ismi_tag.text
                    at_link = at_ismi_tag.get_attribute("href")
                    yas = satir.find_elements(By.TAG_NAME, "td")[2].text
                    kilo = satir.find_element(By.CSS_SELECTOR, "td.kilocell").text
                    jokey = satir.find_element(By.CSS_SELECTOR, "a.bult-black").text

                    jokey_yuzde = jokey_perf_dict.get(jokey, "Bilinmiyor")
                    antrenor_yuzde = antrenor_perf_dict.get(jokey, "Bilinmiyor")
                    sahip_yuzde = sahip_perf_dict.get(jokey, "Bilinmiyor")
                    stil = stil_dict.get(at_ismi.lower(), "Bilinmiyor")

                    kum_kazanc = 0
                    cim_kazanc = 0
                    kilo_farki = "Bilinmiyor"

                    driver.execute_script("window.open(arguments[0]);", at_link)
                    driver.switch_to.window(driver.window_handles[1])
                    time.sleep(2)

                    try:
                        tablo = driver.find_elements(By.CSS_SELECTOR, "table")[0]
                        rows = tablo.find_elements(By.TAG_NAME, "tr")
                        headers = rows[0].find_elements(By.TAG_NAME, "th")
                        kazanc_index = next((i for i, h in enumerate(headers) if "Kazanç" in h.text), -1)
                        if kazanc_index != -1:
                            for r in rows[1:]:
                                cells = r.find_elements(By.TAG_NAME, "td")
                                if len(cells) > kazanc_index:
                                    pist = cells[0].text.strip()
                                    try:
                                        miktar = float(cells[kazanc_index].text.replace("₺", "").replace(".", "").replace(",", "."))
                                        if "Kum" in pist: kum_kazanc = miktar
                                        elif "Çim" in pist: cim_kazanc = miktar
                                    except:
                                        continue
                    except:
                        pass

                    try:
                        tablo = driver.find_elements(By.CSS_SELECTOR, "table")[1]
                        rows = tablo.find_elements(By.TAG_NAME, "tr")
                        if len(rows) >= 3:
                            kilo1 = float(rows[1].find_elements(By.TAG_NAME, "td")[7].text.replace(",", "."))
                            kilo2 = float(rows[2].find_elements(By.TAG_NAME, "td")[7].text.replace(",", "."))
                            kilo_farki = round(kilo1 - kilo2, 2)
                    except:
                        pass

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                    veriler.append([
                        saat, grup, pist_mesafe, at_no, at_ismi, jokey,
                        kum_kazanc, cim_kazanc, kilo_farki,
                        jokey_yuzde, antrenor_yuzde, sahip_yuzde,
                        stil
                    ])
                except:
                    continue

            df = pd.DataFrame(veriler, columns=[
                "Saat", "Grup", "Pist/Mesafe", "At No", "At İsmi", "Jokey",
                "Kum Kazanç", "Çim Kazanç", "Kilo Farkı",
                "Jokey %", "Antrenör Başarı", "Sahip Başarı", "Atın Stili"
            ])
            df_list.append(df)
        except:
            continue

    driver.quit()
    return df_list

def analiz_et(df_list):
    sonuc = []
    for df in df_list:
        df["Puan"] = 0
        df["Puan"] += df["Jokey %"].apply(lambda x: 2 if "%" in str(x) and int(x.replace("%", "")) > 20 else 0)
        df["Puan"] += df["Antrenör Başarı"].apply(lambda x: 1 if "%" in str(x) and int(x.replace("%", "")) > 20 else 0)
        df["Puan"] += df["Sahip Başarı"].apply(lambda x: 1 if "%" in str(x) and int(x.replace("%", "")) > 20 else 0)
        df["Puan"] += df["Kum Kazanç"].apply(lambda x: 2 if isinstance(x, (int, float)) and x > 10000 else 0)
        df["Puan"] += df["Çim Kazanç"].apply(lambda x: 2 if isinstance(x, (int, float)) and x > 10000 else 0)
        df["Puan"] += df["Kilo Farkı"].apply(lambda x: 1 if isinstance(x, float) and x > 0 else 0)
        df["Puan"] += df["Atın Stili"].apply(lambda x: 1 if x in ["En Önde Kaçak", "Öne Yakın"] else 0)

        en_iyi = df[df["Puan"] == df["Puan"].max()].head(1)
        sonuc.append(en_iyi)

    return pd.concat(sonuc).reset_index(drop=True)

def orijin_analizi(df_list):
    tum_df = pd.concat(df_list)
    grup = tum_df.groupby("Jokey")["At İsmi"].count().reset_index(name="Aynı Jokeyli At Sayısı")
    return grup.sort_values(by="Aynı Jokeyli At Sayısı", ascending=False).head(10)
