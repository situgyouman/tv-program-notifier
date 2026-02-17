import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import json
import os
import requests


# --- LINE通知関数 ---
def send_line_multicast(message, channel_access_token, user_id_list):
    if not channel_access_token or not user_id_list:
        print("エラー: LINEトークンまたはユーザーIDが設定されていません。")
        # テスト実行時はコンソールに出力して確認できるようにする
        print("\n--- 送信予定メッセージ ---\n")
        print(message)
        print("\n--------------------------\n")
        return

    line_api_url = 'https://api.line.me/v2/bot/message/multicast'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {channel_access_token}'
    }
    
    if len(message) > 5000:
        message = message[:4990] + "... (文字数超過)"
    
    payload = {
        'to': user_id_list,
        'messages': [{'type': 'text', 'text': message}]
    }
    
    try:
        response = requests.post(line_api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"{len(user_id_list)} 人にメッセージが送信されました。")
    except requests.exceptions.RequestException as e:
        print(f"LINE通知の送信に失敗しました: {e}")

# --- WebDriverセットアップ関数 (タイムアウト対策版) ---
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--log-level=3')
    
    # ★重要: ページの読み込み戦略を 'eager' に設定
    # 画像やサブフレームの読み込み完了を待たずに処理を開始するため、タイムアウトしにくくなる
    options.page_load_strategy = 'eager' 
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30) # 最大読み込み時間を30秒に制限
    return driver

# --- 各番組情報取得関数 ---
# 戻り値を (日付, 本文, URL) のタプルに変更

def get_wbs_highlights(driver):
    url = "https://www.tv-tokyo.co.jp/wbs/"
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "lay-left")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        highlights_section = soup.find("div", class_="lay-left")
        if not highlights_section: return ("日付不明", "「番組の見どころ」セクションが見つかりませんでした。", url)
        
        header = highlights_section.find("h2", class_="hdg")
        date = header.find("span", class_="date").get_text(strip=True) if header else "日付不明"
        
        text_area = highlights_section.find("div", class_="text-area")
        text = text_area.find("p").get_text(strip=True) if text_area else "本文不明"
        
        return (date, text, url)
    except Exception as e:
        return ("取得エラー", f"処理中にエラーが発生: {e}", url)

def get_nms_highlights(driver):
    url = "https://www.tv-tokyo.co.jp/nms/"
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "lay-left")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        highlights_section = soup.find("div", class_="lay-left")
        if not highlights_section: return ("日付不明", "「番組の見どころ」セクションが見つかりませんでした。", url)
        
        header = highlights_section.find("h2", class_="hdg")
        date = header.find("span", class_="date").get_text(strip=True) if header else "日付不明"
        
        text_area = highlights_section.find("div", class_="text-area")
        text = text_area.find("p").get_text(strip=True) if text_area else "本文不明"
        
        return (date, text, url)
    except Exception as e:
        return ("取得エラー", f"処理中にエラーが発生: {e}", url)

def get_money_manabi_info(driver):
    url = "https://www.bs-tvtokyo.co.jp/moneymanabi/"
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tbcms_program-detail.js-program-episode")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        date_tag = soup.find("b", class_="js-program-episode-schedule")
        date = date_tag.get_text(strip=True) if date_tag else "日付不明"
        
        summary_tag = soup.find("div", class_="js-program-episode-comment")
        summary = summary_tag.get_text(strip=True) if summary_tag else "情報が見つかりませんでした。"
        
        return (date, summary, url)
    except Exception as e:
        return ("取得エラー", f"処理中にエラーが発生: {e}", url)

def get_nikkei_next_info(driver):
    url = "https://www.bs-tvtokyo.co.jp/nikkeinext/"
    try:
        driver.get(url)
        # タイムアウト対策済みドライバでアクセス
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "js-program-episode")))
        # 少しだけ待ってDOMの安定を待つ
        time.sleep(2) 
        soup = BeautifulSoup(driver.page_source, "html.parser")

        main_block = soup.find("div", class_="js-program-episode")
        if not main_block:
             return ("日付不明", "情報ブロックが見つかりませんでした。", url)

        # 日時
        date_tag = main_block.find("b", class_="js-program-episode-schedule")
        date = date_tag.get_text(strip=True) if date_tag else "日付不明"
        
        # 見出し（概要）
        comment_tag = main_block.find("div", class_="js-program-episode-comment")
        summary = comment_tag.get_text(separator="\n", strip=True) if comment_tag else ""

        # 詳細本文（番組概要の下を取得）
        detail = ""
        summary_heading = main_block.find("h3", string="番組概要")
        if summary_heading:
            detail_div = summary_heading.find_next_sibling("div", class_="tbcms_program-detail__inner")
            if detail_div:
                p_tag = detail_div.find("p")
                if p_tag:
                    detail = p_tag.get_text(separator="\n", strip=True)

        # 結合
        content_list = []
        if summary: content_list.append(summary)
        if detail: content_list.append(detail)
        full_text = "\n".join(content_list)
        
        if not full_text: full_text = "詳細情報が見つかりませんでした。"

        return (date, full_text, url)

    except Exception as e:
        return ("取得エラー", f"処理中にエラーが発生しました: {e}", url)

def get_cambria_info(driver):
    url = "https://www.tv-tokyo.co.jp/cambria/"
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "hdg-l1-01-wrap")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        info_section = soup.find("div", class_="hdg-l1-01-wrap")
        if not info_section: return ("日付不明", "次回予告セクションが見つかりませんでした。", url)
        
        date = info_section.find("p", class_="date").get_text(strip=True)
        title_tag = info_section.find("h3", class_="title")
        title = title_tag.get_text(separator="\n", strip=True) if title_tag else "タイトル不明"
        
        guest_info = ""
        guest_section = soup.find("ul", class_="list-name")
        if guest_section:
            guest_li = guest_section.find("li")
            if guest_li:
                company = guest_li.find("span", class_="company").get_text(strip=True)
                name = guest_li.find("span", class_="name").get_text(separator=" ", strip=True)
                guest_info = f"\n{company}　　{name}"

        return (date, f"{title}{guest_info}", url)
    except Exception as e:
        return ("取得エラー", f"処理中にエラーが発生: {e}", url)

def get_gaia_info(driver):
    url = "https://www.tv-tokyo.co.jp/gaia/"
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "lyt-hdg-next-inner")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        section = soup.find("div", class_="lyt-hdg-next-inner")
        if not section: return ("日付不明", "次回予告セクションが見つかりませんでした。", url)
        
        date = section.find("p", class_="text").get_text(strip=True)
        title = section.find("h3", class_="title").get_text(strip=True)
        
        return (date, title, url)
    except Exception as e:
        return ("取得エラー", f"処理中にエラーが発生: {e}", url)

def get_gulliver_info(driver):
    url = "https://www.tv-tokyo.co.jp/gulliver/"
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "tbcms_official-contents__heading")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        next_preview_heading = soup.find("h2", class_="tbcms_official-contents__heading", string="次回予告")
        if not next_preview_heading: return ("日付不明", "次回予告が見つかりませんでした。", url)
        
        content_block = next_preview_heading.find_parent("div", class_="tbcms_official-contents__block")
        paragraphs = content_block.find_all("p")
        valid_paragraphs = [p for p in paragraphs if p.get_text(strip=True)]
        
        if len(valid_paragraphs) < 2: return ("日付不明", "放送日や詳細情報が見つかりませんでした。", url)
        
        date_line = valid_paragraphs[0].get_text(strip=True)
        description = valid_paragraphs[1].get_text(strip=True)
        
        return (date_line, description, url)
    except Exception as e:
        return ("取得エラー", f"処理中にエラーが発生: {e}", url)

def get_breakthrough_info(driver):
    url = "https://www.tv-tokyo.co.jp/breakthrough/"
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "js-program-episode-schedule")))
        time.sleep(2) 
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        date_tag = soup.find("b", class_="js-program-episode-schedule")
        date = date_tag.get_text(strip=True) if date_tag else "日時不明"
        
        summary_tag = soup.find("div", class_="js-program-episode-comment")
        summary = summary_tag.get_text(strip=True) if summary_tag else "番組概要が見つかりませんでした。"
        
        return (date, summary, url)
    except Exception as e:
        return ("取得エラー", f"処理中にエラーが発生: {e}", url)

# --- メインの実行部分 ---
if __name__ == "__main__":
    CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
    user_ids_string = os.environ.get('YOUR_USER_ID')
    user_id_list = user_ids_string.split(',') if user_ids_string else []

    # 設定エラーチェック
    if not CHANNEL_ACCESS_TOKEN or not user_id_list:
        print("注意: 環境変数が設定されていないため、LINE送信はスキップされます。")
    
    print("WebDriverを初期化中 (Eager Mode)...")
    driver = setup_driver()
    
    # リストの順番通りに処理
    programs_to_fetch = [
        ("WBS", get_wbs_highlights),
        ("NIKKEI NEWS NEXT", get_nikkei_next_info),
        ("モーサテ", get_nms_highlights),
        ("マネーの学び", get_money_manabi_info),
        ("カンブリア宮殿", get_cambria_info),
        ("ガイアの夜明け", get_gaia_info),
        ("知られざるガリバー", get_gulliver_info),
        ("ブレイクスルー", get_breakthrough_info),
    ]
    
    final_message = "今日のテレビ番組情報です！"
    
    try:
        for name, func in programs_to_fetch:
            print(f"{name}の情報を取得中...")
            # 関数からは (日付, 本文, URL) のタプルが返ってくる
            date, text, url = func(driver)
            
            # ★★★ 改行とフォーマットの修正 ★★★
            # # タイトル #　日付
            # 本文
            # URL
            final_message += f"\n\n" + "="*9 + f"\n# {name} #　{date}\n{text}\n{url}"
            
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
    finally:
        driver.quit()
        print("全ての情報取得が完了しました。")

    send_line_multicast(final_message, CHANNEL_ACCESS_TOKEN, user_id_list)

