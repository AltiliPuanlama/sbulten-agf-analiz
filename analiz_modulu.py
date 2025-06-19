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
import sys

def _get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_tabs_for_city(city_slug):
    driver = _get_driver()
    today = time.strftime("%d-%m-%Y")
    url = f"https://yenibeygir.com/{today}/{city_slug}"
    driver.get(url)
    time.sleep(3)
    tabs = driver.find_elements(By.CSS_SELECTOR, "ul.BultenTabs li")
    tab_list = [(tab.text.strip(), i) for i, tab in enumerate(tabs) if tab.text.strip()]
    driver.quit()
    return tab_list, url

def get_yarislar_from_tab(tab_index, city_url):
    driver = _get_driver()
    driver.get(city_url)
    wait = WebDriverWait(driver, 10)
    time.sleep(3)
    tabs = driver.find_elements(By.CSS_SELECTOR, "ul.BultenTabs li")

    try:
        close_button = driver.find_element(By.CSS_SELECTOR, ".toast-close-button")
        if close_button.is_displayed():
            close_button.click()
            time.sleep(1)
    except:
        pass

    driver.execute_script("arguments[0].click();", tabs[tab_index])
    time.sleep(3)

    yarislar = driver.find_elements(By.CSS_SELECTOR, "div.yarisRow.Popup")
    df_list = []
    kosu_index = 1

    for yaris in yarislar:
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "td.atno")))
        except:
            kosu_index += 1
            continue

        try:
            kosu_no = yaris.find_element(By.CSS_SELECTOR, ".yarisNo").text
            saat = yaris.find_element(By.CSS_SELECTOR, ".yarisSaat span").text
            tur = yaris.find_element(By.CSS_SELECTOR, ".yarisTur").text
            para = yaris.find_element(By.CSS_SELECTOR, ".yarisPara").text
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
                        jokey_yuzde = cells[3].text.strip()
                        antrenor_yuzde = cells[7].text.strip()
                        sahip_yuzde = cells[11].text.strip()
                        jokey_perf_dict[jokey_adi] = jokey_yuzde
                        antrenor_perf_dict[jokey_adi] = antrenor_yuzde
                        sahip_perf_dict[jokey_adi] = sahip_yuzde
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except:
                pass

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
                        stil_kutulari = row.find_elements(By.CSS_SELECTOR, "div.AtStyle > div[title*='%']")
                        max_yuzde = -1
                        baskin_index = -1
                        for i, div in enumerate(stil_kutulari):
                            title = div.get_attribute("title")
                            if '%' in title:
                                try:
                                    parantez_ici = title.split('(')[-1].replace('%)', '').replace('%', '')
                                    yuzde = int(parantez_ici)
                                    if yuzde > max_yuzde:
                                        max_yuzde = yuzde
                                        baskin_index = i
                                except:
                                    continue
                        stil = "Bilinmiyor"
                        if baskin_index == 0:
                            stil = "En Geride"
                        elif baskin_index == 1:
                            stil = "Ortalarda"
                        elif baskin_index == 2:
                            stil = "Öne Yakın"
                        elif baskin_index == 3:
                            stil = "En Önde Kaçak"
                        stil_dict[at_ismi.lower()] = stil
                    except:
                        continue
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except:
                stil_dict = {}

            veriler = []
            at_satirlari = yaris.find_elements(By.CSS_SELECTOR, "tr")
            toplam_at = len(at_satirlari)
            islenen_at = 0

            for satir in at_satirlari:
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

                    driver.execute_script("window.open(arguments[0]);", at_link)
                    driver.switch_to.window(driver.window_handles[1])
                    time.sleep(2)

                    kum_kazanc = 0
                    cim_kazanc = 0
                    try:
                        tablo = driver.find_elements(By.CSS_SELECTOR, "table")[0]
                        satirlar = tablo.find_elements(By.TAG_NAME, "tr")
                        baslik_hucreleri = satirlar[0].find_elements(By.TAG_NAME, "th")
                        kazanc_index = -1
                        for i, hucre in enumerate(baslik_hucreleri):
                            if "Kazanç" in hucre.text:
                                kazanc_index = i
                                break
                        if kazanc_index != -1:
                            for s in satirlar[1:]:
                                hucreler = s.find_elements(By.TAG_NAME, "td")
                                if len(hucreler) > kazanc_index:
                                    pist = hucreler[0].text.strip()
                                    kazanc_text = hucreler[kazanc_index].text.strip().replace("₺", "").replace(".", "").replace(",", ".")
                                    try:
                                        kazanc = float(kazanc_text)
                                        if "Kum" in pist:
                                            kum_kazanc = kazanc
                                        elif "Çim" in pist:
                                            cim_kazanc = kazanc
                                    except:
                                        continue
                    except:
                        pass

                    kilo_farki = "Bilinmiyor"
                    try:
                        tablo = driver.find_elements(By.CSS_SELECTOR, "table")[1]
                        rows = tablo.find_elements(By.TAG_NAME, "tr")
                        if len(rows) >= 3:
                            bugun_kilo = float(rows[1].find_elements(By.TAG_NAME, "td")[7].text.replace(",", "."))
                            onceki_kilo = float(rows[2].find_elements(By.TAG_NAME, "td")[7].text.replace(",", "."))
                            kilo_farki = round(bugun_kilo - onceki_kilo, 2)
                    except:
                        pass

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                    veriler.append([
                        kosu_no, saat, tur, para, grup, pist_mesafe,
                        at_no, at_ismi, yas, kilo, jokey,
                        kum_kazanc, cim_kazanc, kilo_farki,
                        jokey_yuzde, antrenor_yuzde, sahip_yuzde, stil
                    ])
                except:
                    continue

                islenen_at += 1
                progress = int((islenen_at / toplam_at) * 100)
                sys.stdout.write(f"\r{kosu_index}. Koşu işleniyor... %{progress}")
                sys.stdout.flush()

            if veriler:
                df = pd.DataFrame(veriler, columns=[
                    "Koşu No", "Saat", "Yarış Türü", "Ödül", "Grup", "Pist/Mesafe",
                    "At No", "At İsmi", "Yaş", "Kilo", "Jokey",
                    "Kum Kazanç", "Çim Kazanç", "Kilo Farkı",
                    "Jokey %", "Antrenör Başarı", "Sahip Başarı", "Atın Stili"
                ])
                df_list.append(df)
            kosu_index += 1

        except Exception as e:
            kosu_index += 1
            continue

    driver.quit()
    return df_list
