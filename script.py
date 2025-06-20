from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import datetime

def yarislari_cek(url=None):
    # === 1. Tarih ve Şehir Al ===
    if url is None:
        print("\nYarış verilerini çekmek için tarih ve şehir belirtiniz.")
        secilen_tarih = input("Tarih (GG-AA-YYYY): ").strip()
        secilen_sehir = input("Şehir (küçük harf, örn: istanbul, ankara): ").strip().lower()

        if not secilen_tarih or not secilen_sehir:
            print("Tarih veya şehir boş bırakılamaz.")
            return {}

        try:
            datetime.datetime.strptime(secilen_tarih, "%d-%m-%Y")
        except ValueError:
            print("Tarih formatı hatalı! GG-AA-YYYY şeklinde giriniz.")
            return {}

        url = f"https://yenibeygir.com/{secilen_tarih}/{secilen_sehir}"

    print(f"\n🔗 Veri çekilecek adres: {url}\n")

    # === 2. Tarayıcı ayarları ===
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")  # ✅ EKLENDİ
    options.add_argument("--disable-dev-shm-usage")  # ✅ EKLENDİ

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    time.sleep(2)

    try:
        toast = driver.find_element(By.CLASS_NAME, "toast-bottom-content")
        driver.execute_script("arguments[0].remove();", toast)
    except:
        pass

    kosular = {}
    yarislar = driver.find_elements(By.CSS_SELECTOR, "div.yarisRow.Popup")
    kosu_index = 1

    for yaris in yarislar:
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "td.atno")))
        except:
            kosu_index += 1
            continue

        try:
            jokey_perf_dict = {}
            antrenor_perf_dict = {}
            sahip_perf_dict = {}
            stil_dict = {}

            try:
                jokey_link = yaris.find_element(By.CSS_SELECTOR, "a.yaris-jokeyperformans").get_attribute("href")
                driver.execute_script("window.open(arguments[0]);", jokey_link)
                driver.switch_to.window(driver.window_handles[1])
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr")))
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 11:
                        jokey = cells[1].text.strip()
                        jokey_perf_dict[jokey] = cells[3].text.strip()
                        antrenor_perf_dict[jokey] = cells[7].text.strip()
                        sahip_perf_dict[jokey] = cells[11].text.strip()
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except:
                pass

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
                                    yuzde = int(title.split('(')[-1].replace('%)', '').replace('%', ''))
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
                pass

            veriler = []
            at_satirlari = yaris.find_elements(By.CSS_SELECTOR, "tr")

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
                    kilo_farki = "Bilinmiyor"

                    try:
                        tablo = driver.find_elements(By.CSS_SELECTOR, "table")[0]
                        rows = tablo.find_elements(By.TAG_NAME, "tr")
                        kazanc_index = next((i for i, th in enumerate(rows[0].find_elements(By.TAG_NAME, "th")) if "Kazanç" in th.text), -1)
                        for s in rows[1:]:
                            hucreler = s.find_elements(By.TAG_NAME, "td")
                            if kazanc_index != -1 and len(hucreler) > kazanc_index:
                                pist = hucreler[0].text.strip()
                                kazanc = float(hucreler[kazanc_index].text.replace("₺", "").replace(".", "").replace(",", "."))
                                if "Kum" in pist:
                                    kum_kazanc = kazanc
                                elif "Çim" in pist:
                                    cim_kazanc = kazanc
                    except:
                        pass

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
                kosular[kosu_index] = df
        except:
            pass
        kosu_index += 1

    driver.quit()
    return kosular
