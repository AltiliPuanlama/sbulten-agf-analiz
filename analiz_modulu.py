# analiz_modulu.py

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
    driver.execute_script("arguments[0].click();", tabs[tab_index])
    time.sleep(3)

    yarislar = driver.find_elements(By.CSS_SELECTOR, "div.yarisRow.Popup")
    df_list = []

    for yaris in yarislar:
        try:
            saat = yaris.find_element(By.CSS_SELECTOR, ".yarisSaat span").text
            grup = yaris.find_element(By.CSS_SELECTOR, ".yarisGrup span").text
            pist_mesafe = "Bilinmiyor"
            try:
                pist_mesafe = yaris.find_element(By.CSS_SELECTOR, ".kumpist").text
            except:
                try:
                    pist_mesafe = yaris.find_element(By.CSS_SELECTOR, ".cimpist").text
                except:
                    pass

            jokey_perf, antrenor_perf, sahip_perf = {}, {}, {}
            try:
                link = yaris.find_element(By.CSS_SELECTOR, "a.yaris-jokeyperformans").get_attribute("href")
                driver.execute_script("window.open(arguments[0]);", link)
                driver.switch_to.window(driver.window_handles[1])
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr")))
                for row in driver.find_elements(By.CSS_SELECTOR, "table tbody tr"):
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 12:
                        isim = cells[1].text.strip()
                        jokey_perf[isim] = cells[3].text.strip()
                        antrenor_perf[isim] = cells[7].text.strip()
                        sahip_perf[isim] = cells[11].text.strip()
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except:
                pass

            stil_dict = {}
            try:
                link = yaris.find_element(By.CSS_SELECTOR, "a.yaris-stil").get_attribute("href")
                driver.execute_script("window.open(arguments[0]);", link)
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(2)
                for row in driver.find_elements(By.CSS_SELECTOR, "table.StillerTable tbody tr"):
                    try:
                        at_ismi = row.find_element(By.CSS_SELECTOR, "a.atisimlink").text.strip().lower()
                        kutular = row.find_elements(By.CSS_SELECTOR, "div.AtStyle > div[title*='%']")
                        max_yuzde, baskin = -1, -1
                        for i, div in enumerate(kutular):
                            try:
                                yuzde = int(re.findall(r"%([0-9]+)", div.get_attribute("title"))[0])
                                if yuzde > max_yuzde:
                                    max_yuzde, baskin = yuzde, i
                            except:
                                continue
                        stil = ["En Geride", "Ortalarda", "Öne Yakın", "En Önde Kaçak"]
                        stil_dict[at_ismi] = stil[baskin] if 0 <= baskin < len(stil) else "Bilinmiyor"
                    except:
                        continue
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except:
                pass

            veriler = []
            for satir in yaris.find_elements(By.CSS_SELECTOR, "tr"):
                try:
                    at_no = satir.find_element(By.CSS_SELECTOR, "td.atno").text
                    at_tag = satir.find_element(By.CSS_SELECTOR, "a.atisimlink")
                    at_ismi = at_tag.text
                    at_link = at_tag.get_attribute("href")
                    kilo = satir.find_element(By.CSS_SELECTOR, "td.kilocell").text
                    yas = satir.find_elements(By.TAG_NAME, "td")[2].text
                    jokey = satir.find_element(By.CSS_SELECTOR, "a.bult-black").text

                    jokey_yuzde = jokey_perf.get(jokey, "Bilinmiyor")
                    ant_yuzde = antrenor_perf.get(jokey, "Bilinmiyor")
                    sahip_yuzde = sahip_perf.get(jokey, "Bilinmiyor")
                    stil = stil_dict.get(at_ismi.lower(), "Bilinmiyor")

                    driver.execute_script("window.open(arguments[0]);", at_link)
                    driver.switch_to.window(driver.window_handles[1])
                    time.sleep(2)

                    kum_kazanc = cim_kazanc = 0
                    try:
                        tablo = driver.find_elements(By.CSS_SELECTOR, "table")[0]
                        headers = tablo.find_elements(By.TAG_NAME, "th")
                        kazanc_index = next((i for i, h in enumerate(headers) if "Kazanç" in h.text), -1)
                        for row in tablo.find_elements(By.TAG_NAME, "tr")[1:]:
                            tds = row.find_elements(By.TAG_NAME, "td")
                            if kazanc_index != -1 and len(tds) > kazanc_index:
                                pist = tds[0].text.strip()
                                try:
                                    val = float(tds[kazanc_index].text.replace("₺", "").replace(".", "").replace(",", "."))
                                    if "Kum" in pist:
                                        kum_kazanc = val
                                    elif "Çim" in pist:
                                        cim_kazanc = val
                                except:
                                    continue
                    except:
                        pass

                    kilo_farki = "Bilinmiyor"
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
                        jokey_yuzde, ant_yuzde, sahip_yuzde, stil
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
        en_iyi = df.sort_values(by="Puan", ascending=False).head(1)
        sonuc.append(en_iyi)
    return pd.concat(sonuc)


def orijin_analizi(df_list):
    tum_df = pd.concat(df_list)
    grup = tum_df.groupby("Jokey")["At İsmi"].count().reset_index(name="Aynı Jokeyli At Sayısı")
    return grup.sort_values(by="Aynı Jokeyli At Sayısı", ascending=False).head(10)
