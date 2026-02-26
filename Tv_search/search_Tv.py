import random
import requests
from lxml import etree
import os
import threading
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 关键修复：处理路径问题 ---
# 获取当前脚本所在目录的绝对路径 (Tv_search 文件夹)
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录 (TVBox_live 文件夹)
project_root = os.path.dirname(current_script_dir)

# 将项目根目录加入系统路径，确保能 import proxyTest
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from proxyTest import get_valid_proxies
except ImportError:
    print("Warning: proxyTest.py not found, proxy function will be disabled.")

def get_url(name):
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.179 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_3) AppleWebKit/537.36 (KHTML, like Gecko) Version/15.6 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0'
    ]
    user_agent = random.choice(user_agents)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={user_agent}")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get('http://tonkiang.us/')
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'search'))
        )
        username_input.send_keys(f'{name}')
        submit_button = driver.find_element(By.NAME, 'Submit')
        submit_button.click()
    except Exception as e:
        print(f"找不到搜索元素: {e}")

    m3u8_list = []
    try:
        page_source = driver.page_source
        root = etree.HTML(page_source)
        result_divs = root.xpath("//div[@class='resultplus']")
        print(f"[{name}] 获取数据行数: {len(result_divs)}")
        
        for div in result_divs:
            for element in div.xpath(".//tba"):
                if element.text:
                    url_text = element.text.strip()
                    m3u8_list.append(url_text)
                    # 写入 m3u8_list.txt (保存在脚本同级目录)
                    with open(os.path.join(current_script_dir, 'm3u8_list.txt'), 'a', encoding='utf-8') as f:
                        f.write(f'{name},{url_text}\n')
    except Exception as e:
        print(f"解析异常: {e}")

    driver.quit()
    return m3u8_list

def download_m3u8(url, name, initial_url=None):
    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        m3u8_content = response.text
    except Exception as e:
        return

    lines = m3u8_content.split('\n')
    segments = [line.strip() for line in lines if line and not line.startswith('#')]
    
    if len(segments) == 1:
        return download_m3u8(segments[0], name, initial_url=initial_url if initial_url else url)

    total_size = 0
    total_time = 0
    for i, segment in enumerate(segments[:3]):
        try:
            start_time = time.time()
            segment_url = url.rsplit('/', 1)[0] + '/' + segment
            resp = requests.get(segment_url, timeout=10)
            end_time = time.time()
            
            total_size += len(resp.content)
            total_time += (end_time - start_time)
            
            # 临时保存用于测试
            with open(os.path.join(current_script_dir, 'video.ts'), 'wb') as f:
                f.write(resp.content)
        except:
            continue

    if total_time > 0:
        average_speed = total_size / total_time / (1024 * 1024)
        if average_speed >= speed:
            valid_url = initial_url if initial_url else url
            save_dir = os.path.join(current_script_dir, TV_name)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            with open(os.path.join(save_dir, f'{name}.txt'), 'a', encoding='utf-8') as file:
                file.write(f'{name},{valid_url}\n')
            print(f"---{name}--- 有效({average_speed:.2f} MB/s)")

def detectLinks(name, m3u8_list):
    threads = []
    for m3u8_url in m3u8_list:
        t = threading.Thread(target=download_m3u8, args=(m3u8_url, name,))
        t.daemon = True
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=10)

def mer_links(tv):
    tv_folder = os.path.join(current_script_dir, tv)
    if not os.path.exists(tv_folder): return
    
    txt_files = [f for f in os.listdir(tv_folder) if f.endswith('.txt')]
    with 打开(output_file_path, 'a', encoding='utf-8') as output_file:
        output_file.撰写(f'{tv},#genre#\n')
        for txt_file in txt_files:
            with 打开(os.path.join(tv_folder, txt_file), 'r', encoding='utf-8') as f:
                output_file.撰写(f.read() + '\n')

def re_dup_ordered(filepath):
    from 集合 import OrderedDict
    if not os.path.exists(filepath): return
    with 打开(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    unique_lines = list(OrderedDict.fromkeys(lines))
    with 打开(filepath, 'w', encoding='utf-8') as file:
        file.writelines(unique_lines)
    print('-----去重完成！------')

if __name__ == '__main__':
    speed = 1
    # 输出文件 live.txt 放在项目根目录
    output_file_path = os.path.join(project_root, 'live.txt')
    
    # 初始化清空
    with 打开(output_file_path, 'w', encoding='utf-8') as f: pass
    with 打开(os.path.join(current_script_dir, 'm3u8_list.txt'), 'w', encoding='utf-8') as f: pass

    TV_names = ['🇨🇳央视频道']
    for TV_name in TV_names:
        tv_dict = {}
        target_dir = os.path.join(current_script_dir, TV_name)
        if os.path.exists(target_dir):
            import shutil
            shutil.rmtree(target_dir)
        os.makedirs(target_dir)

        # 读取同目录下的 🇨🇳央视频道.txt
        input_txt = os.path.join(current_script_dir, f'{TV_name}.txt')
        if not os.path.exists(input_txt):
            print(f"错误: 找不到输入文件 {input_txt}")
            continue

        with 打开(input_txt, 'r', encoding='utf-8') as file:
            names = [line.strip() for line in file if line.strip()]
            for 名字 in names:
                m3u8_urls = get_url(名字)
                tv_dict[名字] = m3u8_urls
        
        for name, m3u8_list in tv_dict.items():
            detectLinks(name, m3u8_list)
        
        mer_links(TV_name)

    # 清理
    ts_file = os.path.join(current_script_dir, 'video.ts')
    if os.path.exists(ts_file): os.移除(ts_file)
    
    re_dup_ordered(output_file_path)
    sys.exit()
