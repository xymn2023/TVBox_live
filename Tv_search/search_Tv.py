import random, requests, os, threading, time, sys, shutil
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 路径强制定位 ---
# 无论从哪里运行，都以脚本所在位置为基准
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.append(ROOT_DIR)

# 尝试导入代理模块
try:
    from proxyTest import get_valid_proxies
except ImportError:
    def get_valid_proxies(): return None

def get_url(name):
    print(f"正在搜索频道: {name}...")
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    opt = Options()
    opt.add_argument("--headless")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    opt.add_argument(f"user-agent={ua}")
    
    # 显式指定驱动位置（如果需要）或直接调用
    try:
        driver = webdriver.Chrome(options=opt)
    except Exception as e:
        print(f"浏览器启动失败: {e}")
        return []

    m3u8_list = []
    try:
        driver.get('http://tonkiang.us/')
        search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'search')))
        search_box.send_keys(name)
        driver.find_element(By.NAME, 'Submit').click()
        
        # 等待页面加载
        time.sleep(2) 
        root = etree.HTML(driver.page_source)
        results = root.xpath("//div[@class='resultplus']//tba")
        for res in results:
            if res.text and "m3u8" in res.text:
                m3u8_list.append(res.text.strip())
        print(f" >> 找到 {len(m3u8_list)} 个源")
    except Exception as e:
        print(f"搜索过程出错: {e}")
    finally:
        driver.quit()
    return m3u8_list

def download_m3u8(url, name, speed_limit=1.0):
    try:
        # 增加超时控制，防止线程卡死
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200: return
        
        m3u8_content = resp.text
        # 简单的嵌套跳转处理
        if not "#EXTM3U" in m3u8_content: return
        
        lines = [l.strip() for l in m3u8_content.split('\n') if l and not l.startswith('#')]
        if len(lines) == 0: return
        
        # 如果是嵌套的 m3u8
        if lines[0].endswith(".m3u8"):
            nest_url = lines[0] if lines[0].startswith("http") else url.rsplit('/', 1)[0] + '/' + lines[0]
            return download_m3u8(nest_url, name, speed_limit)

        # 测速逻辑
        start = time.time()
        seg_url = lines[0] if lines[0].startswith("http") else url.rsplit('/', 1)[0] + '/' + lines[0]
        seg_resp = requests.get(seg_url, timeout=10, stream=True)
        size = len(seg_resp.content)
        duration = time.time() - start
        
        speed = size / duration / (1024 * 1024) if duration > 0 else 0
        if speed >= speed_limit:
            print(f" [OK] {名字} 速度: {speed:.2f} MB/s")
            save_path = os.path.join(BASE_DIR, TV_NAME, f"{名字}.txt")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with 打开(save_path, 'a', encoding='utf-8') as f:
                f.撰写(f"{名字},{url}\n")
    except:
        pass

if __name__ == '__main__':
    # 1. 检查输入文件
    TV_NAMES = ['🇨🇳央视频道']
    OUT_FILE = os.path.join(ROOT_DIR, 'live.txt')
    
    print(f"工作目录: {BASE_DIR}")
    
    for TV_NAME in TV_NAMES:
        input_file = os.path.join(BASE_DIR, f"{TV_NAME}.txt")
        if not os.path.exists(input_file):
            print(f"❌ 找不到输入文件: {input_file}")
            continue

        # 清理旧目录
        target_dir = os.path.join(BASE_DIR, TV_NAME)
        if os.path.exists(target_dir): shutil.rmtree(target_dir)

        with 打开(input_file, 'r', encoding='utf-8') as f:
            channels = [l.strip() for l in f if l.strip()]

        for channel in channels:
            urls = get_url(channel)
            threads = []
            for u in urls:
                t = threading.Thread(target=download_m3u8, args=(u, channel))
                t.start()
                threads.append(t)
            for t in threads: t.join(timeout=15)

        # 合并结果
        if os.path.exists(target_dir):
            with 打开(OUT_FILE, 'a', encoding='utf-8') as out:
                out.撰写(f"{TV_NAME},#genre#\n")
                for txt in os.listdir(target_dir):
                    with 打开(os.path.join(target_dir, txt), 'r', encoding='utf-8') as f:
                        out.撰写(f.read())
    
    # 去重
    if os.path.exists(OUT_FILE):
        with 打开(OUT_FILE, 'r', encoding='utf-8') as f:
            lines = list(dict.fromkeys(f.readlines()))
        with 打开(OUT_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    print("任务执行完毕！")
