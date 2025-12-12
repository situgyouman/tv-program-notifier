import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import os
import requests

# --- LINE通知関数 ---
def send_line_multicast(message, channel_access_token, user_id_list):
    if not channel_access_token or not user_id_list:
        print("エラー: LINEトークンまたはユーザーIDが設定されていません。")
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

# --- WebDriverセットアップ関数 ---
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--log-level=3')
    driver = webdriver.Chrome(options=options)
    return driver

# --- 各番組情報取得関数 ---

def get_wbs_highlights(driver):
    url = "https://www.tv-tokyo.co.jp/wbs/"
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "lay-left")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        highlights_section = soup.find("div", class_="lay-left")
        if not highlights_section: return f"WBS: 「番組の見どころ」セクションが見つかりませんでした。\n{url}"
        header = highlights_section.find("h2", class_="hdg")
        date = header.find("span", class_="date").get_text(strip=True) if header else "日付不明"
        text_area = highlights_section.find("div", class_="text-area")
        text = text_area.find("p").get_text(strip=True) if text_area else "本文不明"
        return f"{date}\n{text}\n{url}"
    except Exception as e:
        return f"WBSの処理中にエラーが発生: {e}\n{url}"

def get_nms_highlights(driver):
    url = "https://www.tv-tokyo.co.jp/nms/"
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "lay-left")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        highlights_section = soup.find("div", class_="lay-left")
        if not highlights_section: return f"モーサテ: 「番組の見どころ」セクションが見つかりませんでした。\n{url}"
        header = highlights_section.find("h2", class_="hdg")
        date = header.find("span", class_="date").get_text(strip=True) if header else "日付不明"
        text_area = highlights_section.find("div", class_="text-area")
        text = text_area.find("p").get_text(strip=True) if text_area else "本文不明"
        return f"{date}\n{text}\n{url}"
    except Exception as e:
        return f"モーサテの処理中にエラーが発生: {e}\n{url}"

def get_money_manabi_info(driver):
    url = "https://www.bs-tvtokyo.co.jp/moneymanabi/"
    for i in range(3):
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.tbcms_program-detail.js-program-episode"))
            )
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            date_tag = soup.find("b", class_="js-program-episode-schedule")
            summary_tag = soup.find("div", class_="js-program-episode-comment")

            if date_tag and date_tag.get_text(strip=True) and summary_tag and summary_tag.get_text(strip=True):
                date = date_tag.get_text(strip=True)
                summary = summary_tag.get_text(strip=True)
                return f"{date}\n{summary}\n{url}"
            else:
                return f"マネーの学び: 次回予告の情報が見つかりませんでした。\n\n{url}"

        except TimeoutException:
            return f"マネーの学び: 次回予告の情報が見つかりませんでした。\n\n{url}"
        except Exception as e:
            print(f"マネーの学び: 試行 {i+1} 回目でエラーが発生: {e}")
            if i < 2: time.sleep(3)
            else: return f"マネーの学びの処理中にエラーが解決しませんでした: {e}\n{url}"
    
    return f"マネーの学び: 複数回試行しましたが情報を取得できませんでした。\n{url}"

# ★★★ NIKKEI NEWS NEXT の取得関数（修正版：番組概要を特定して取得） ★★★
def get_nikkei_next_info(driver):
    url = "https://www.bs-tvtokyo.co.jp/nikkeinext/"
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "js-program-episode")))
        time.sleep(1) 
        soup = BeautifulSoup(driver.page_source, "html.parser")

        main_block = soup.find("div", class_="js-program-episode")
        if not main_block:
             return f"NIKKEI NEWS NEXT: 情報ブロックが見つかりませんでした。\n\n{url}"

        # 1. 日時の取得
        date_tag = main_block.find("b", class_="js-program-episode-schedule")
        date = date_tag.get_text(strip=True) if date_tag else "日時不明"
        
        # 2. 見出し（概要）の取得
        comment_tag = main_block.find("div", class_="js-program-episode-comment")
        summary = comment_tag.get_text(separator="\n", strip=True) if comment_tag else ""

        # 3. 「番組概要」セクションの詳細本文の取得
        detail = ""
        # "番組概要"という文字を含むh3タグを探す
        summary_heading = main_block.find("h3", string="番組概要")
        
        if summary_heading:
            # その次にあるdivタグの中身を取得する
            detail_div = summary_heading.find_next_sibling("div", class_="tbcms_program-detail__inner")
            if detail_div:
                p_tag = detail_div.find("p")
                if p_tag:
                    detail = p_tag.get_text(separator="\n", strip=True)
                    # ご希望の形式に合わせて「番組概要」という見出しも本文の前に追加
                    detail = "番組概要\n" + detail

        content = []
        if summary: content.append(summary)
        if detail: content.append(detail)
        full_content = "\n".join(content)

        if date == "日時不明" and not full_content:
             return f"NIKKEI NEWS NEXT: 次回予告の情報が見つかりませんでした。\n\n{url}"

        return f"{date}\n{full_content}\n{url}"
    except Exception as e:
        return f"NIKKEI NEWS NEXTの処理中にエラーが発生: {e}\n{url}"


def get_cambria_info(driver):
    url = "https://www.tv-tokyo.co.jp/cambria/"
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "hdg-l1-01-wrap")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        info_section = soup.find("div", class_="hdg-l1-01-wrap")
        if not info_section: 
            return f"カンブリア宮殿: 次回予告セクションが見つかりませんでした。\n{url}"
        date = info_section.find("p", class_="date").get_text(strip=True)
        title_tag = info_section.find("h3", class_="title")
        title = title_tag.get_text(separator="\n", strip=True) if title_tag else "タイトル不明"
        
        guest_info = ""
        guest_section = soup.find("ul", class_="list-name")
        if guest_section:
            guest_li = guest_section.find("li")
            if guest_li:
                company_span = guest_li.find("span", class_="company")
                name_span = guest_li.find("span", class_="name")
                if company_span and name_span:
                    company = company_span.get_text(strip=True)
                    name = name_span.get_text(separator=" ", strip=True)
                    guest_info = f"{company}　　{name}"

        result = f"次回のカンブリア宮殿は {date}\n{title}"
        if guest_info:
            result += f"\n{guest_info}"
        result += f"\n{url}"
        return result
    except Exception as e:
        return f"カンブリア宮殿の処理中にエラーが発生: {e}\n{url}"

def get_gaia_info(driver):
    url = "https://www.tv-tokyo.co.jp/gaia/"
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "lyt-hdg-next-inner")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        section = soup.find("div", class_="lyt-hdg-next-inner")
        if not section: return f"ガイアの夜明け: 次回予告セクションが見つかりませんでした。\n{url}"
        date = section.find("p", class_="text").get_text(strip=True)
        title = section.find("h3", class_="title").get_text(strip=True)
        return f"{date}\n{title}\n{url}"
    except Exception as e:
        return f"ガイアの夜明けの処理中にエラーが発生: {e}\n{url}"

def get_gulliver_info(driver):
    url = "https://www.tv-tokyo.co.jp/gulliver/"
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "tbcms_official-contents__heading")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        next_preview_heading = soup.find("h2", class_="tbcms_official-contents__heading", string="次回予告")
        if not next_preview_heading: return f"ガリバー: 「次回予告」の見出しが見つかりませんでした。\n{url}"
        content_block = next_preview_heading.find_parent("div", class_="tbcms_official-contents__block")
        if not content_block: return f"ガリバー: コンテンツブロックが見つかりませんでした。\n{url}"
        paragraphs = content_block.find_all("p")
        valid_paragraphs = [p for p in paragraphs if p.get_text(strip=True)]
        if len(valid_paragraphs) < 2: return f"ガリバー: 放送日や詳細情報が見つかりませんでした。\n{url}"
        date_line = valid_paragraphs[0].get_text(strip=True)
        description = valid_paragraphs[1].get_text(strip=True)
        return f"{date_line}\n{description}\n{url}"
    except Exception as e:
        return f"ガリバーの処理中にエラーが発生: {e}\n{url}"

def get_breakthrough_info(driver):
    url = "https://www.tv-tokyo.co.jp/breakthrough/"
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "js-program-episode-schedule")))
        time.sleep(1) 
        soup = BeautifulSoup(driver.page_source, "html.parser")
        date_tag = soup.find("b", class_="js-program-episode-schedule")
        date = date_tag.get_text(strip=True) if date_tag and date_tag.get_text(strip=True) else "日時不明"
        summary_tag = soup.find("div", class_="js-program-episode-comment")
        summary = summary_tag.get_text(strip=True) if summary_tag and summary_tag.get_text(strip=True) else "番組概要が見つかりませんでした。"
        if date == "日時不明" or summary == "番組概要が見つかりませんでした。":
             return f"ブレイクスルー: 次回予告の情報が見つかりませんでした。\n\n{url}"
        return f"{date}\n{summary}\n{url}"
    except Exception as e:
        return f"ブレイクスルーの処理中にエラーが発生: {e}\n{url}"

# --- メインの実行部分 ---
if __name__ == "__main__":
    # 環境変数の取得
    CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
    user_ids_string = os.environ.get('YOUR_USER_ID')
    user_id_list = user_ids_string.split(',') if user_ids_string else []

    if not CHANNEL_ACCESS_TOKEN or not user_id_list:
        print("エラー: 必要な環境変数（アクセストークンまたはユーザーID）が設定されていません。")
        print("環境変数 CHANNEL_ACCESS_TOKEN と YOUR_USER_ID を設定してください。")
    else:
        print("WebDriverを初期化・自動管理しています...")
        driver = setup_driver()
        
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
                info = func(driver)
                final_message += f"\n\n" + "="*9 + f"\n# {name} #\n{info}"
        except Exception as e:
            print(f"予期せぬエラーが発生しました: {e}")
        finally:
            driver.quit()
            print("全ての情報取得が完了しました。")

        # print(final_message) 
        send_line_multicast(final_message, CHANNEL_ACCESS_TOKEN, user_id_list)
