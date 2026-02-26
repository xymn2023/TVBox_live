import random, requests, os, threading, time, sys, shutil
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Path Config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.append(ROOT_DIR)

def get_driver():
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    opt = Options()
    opt.add_argument("--headless")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    opt.add_argument(f"user-agent={ua}")
    return webdriver.Chrome(options=opt)

def get_url(name):
    print(f"Searching: {name}")
    driver = get_driver()
    m3u8_list = []
    try:
        driver.get('http://tonkiang.us/')
        search_box = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'search')))
        search_box.send_keys(name)
        driver.find_element(By.NAME, 'Submit').click()
        time.sleep(3) 
        root = etree.HTML(driver.page_source)
        results = root.xpath("//div[@class='resultplus']//tba")
        for res in results:
            if res.text and "m3u8" in res.text:
                m3u8_list.append(res.text.strip())
    except Exception as e:
        print(f"Error searching {name}: {e}")
    finally:
        driver.quit()
    return m3u8_list

def download_m3u8(url, name, speed_limit=1.0):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200: return
        lines = [l.strip() for l in resp.text.split('\n') if l and not l.startswith('#')]
        if not lines: return
        
        target = lines[0] if lines[0].startswith("http") else url.rsplit('/', 1)[0] + '/' + lines[0]
        start = time.time()
        seg_resp = requests.get(target, timeout=10, stream=True)
        speed = len(seg_resp.content) / (time.time() - start) / (1024 * 1024)
        
        if speed >= speed_limit:
            save_dir = os.path.join(BASE_DIR, TV_NAME)
            os.makedirs(save_dir, exist_ok=True)
            with open(os.path.join(save_dir, f"{name}.txt"), 'a', encoding='utf-8') as f:
                f.write(f"{name},{url}\n")
    except:
        pass

if __name__ == '__main__':
    TV_NAMES = ['🇨🇳央视频道']
    OUT_FILE = os.path.join(ROOT_DIR, 'live.txt')
    
    # Init OUT_FILE
    with open(OUT_FILE, 'w', encoding='utf-8') as f: pass

    for TV_NAME in TV_NAMES:
        input_file = os.path.join(BASE_DIR, f"{TV_NAME}.txt")
        if not os.path.exists(input_file): continue
        
        tmp_dir = os.path.join(BASE_DIR, TV_NAME)
        if os.path.exists(tmp_dir): shutil.rmtree(tmp_dir)

        with open(input_file, 'r', encoding='utf-8') as f:
            channels = [l.strip() for l in f if l.strip()]

        for channel in channels:
            urls = get_url(channel)
            threads = [threading.Thread(target=download_m3u8, args=(u, channel)) for u in urls]
            for t in threads: t.start()
            for t in threads: t.join(timeout=20)

        if os.path.exists(tmp_dir):
            with open(OUT_FILE, 'a', encoding='utf-8') as out:
                out.write(f"{TV_NAME},#genre#\n")
                for txt in os.listdir(tmp_dir):
                    with open(os.path.join(tmp_dir, txt), 'r', encoding='utf-8') as f:
                        out.write(f.read())

    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, 'r', encoding='utf-8') as f:
            lines = list(dict.fromkeys(f.readlines()))
        with open(OUT_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    print("Done")
