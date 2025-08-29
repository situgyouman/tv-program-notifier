import requests
import json
import os
from bs4 import BeautifulSoup

# --- 通知を送る関数 (一斉送信対応) ---
def send_line_multicast(message, channel_access_token, user_id_list):
    """
    LINE Messaging APIを使って複数人にプッシュメッセージを送信する関数
    """
    line_api_url = 'https://api.line.me/v2/bot/message/multicast'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {channel_access_token}'
    }
    payload = {
        'to': user_id_list,
        'messages': [{'type': 'text', 'text': message}]
    }
    requests.post(line_api_url, headers=headers, data=json.dumps(payload))

# --- 各番組の情報を取得する関数 (URL追加などの修正版) ---

def get_wbs_highlights():
    url = "https://www.tv-tokyo.co.jp/wbs/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        highlights_section = soup.find("div", class_="lay-left")
        if not highlights_section: return "WBS: 「番組の見どころ」セクションが見つかりませんでした。"
        header = highlights_section.find("h2", class_="hdg")
        title = header.find("span", class_="title").get_text(strip=True) if header else "見出し不明"
        date = header.find("span", class_="date").get_text(strip=True) if header else "日付不明"
        text_area = highlights_section.find("div", class_="text-area")
        text = text_area.find("p").get_text(strip=True) if text_area else "本文不明"
        # 取得した情報とURLを結合して返す
        return f"--- {title} ---\n{date}\n{text}\n\n{url}"
    except Exception as e:
        return f"WBSの処理中にエラーが発生: {e}\n\n{url}"

def get_nms_highlights():
    url = "https://www.tv-tokyo.co.jp/nms/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        highlights_section = soup.find("div", class_="lay-left")
        if not highlights_section: return "モーサテ: 「番組の見どころ」セクションが見つかりませんでした。"
        header = highlights_section.find("h2", class_="hdg")
        title = header.find("span", class_="title").get_text(strip=True) if header else "見出し不明"
        date = header.find("span", class_="date").get_text(strip=True) if header else "日付不明"
        text_area = highlights_section.find("div", class_="text-area")
        text = text_area.find("p").get_text(strip=True) if text_area else "本文不明"
        return f"--- {title} ---\n{date}\n{text}\n\n{url}"
    except Exception as e:
        return f"モーサテの処理中にエラーが発生: {e}\n\n{url}"

def get_cambria_info():
    url = "https://www.tv-tokyo.co.jp/cambria/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        section = soup.find("div", class_="hdg-l1-01-wrap")
        if not section: return "カンブリア宮殿: 次回予告セクションが見つかりませんでした。"
        date = section.find("p", class_="date").get_text(strip=True)
        title_tag = section.find("h3", class_="title")
        title = title_tag.get_text(separator="\n", strip=True) if title_tag else "タイトル不明"
        return f"次回のカンブリア宮殿は {date}\n{title}\n\n{url}"
    except Exception as e:
        return f"カンブリア宮殿の処理中にエラーが発生: {e}\n\n{url}"

def get_gaia_info():
    url = "https://www.tv-tokyo.co.jp/gaia/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        section = soup.find("div", class_="lyt-hdg-next-inner")
        if not section: return "ガイアの夜明け: 次回予告セクションが見つかりませんでした。"
        date = section.find("p", class_="text").get_text(strip=True)
        title = section.find("h3", class_="title").get_text(strip=True)
        return f"{date}\n{title}\n\n{url}"
    except Exception as e:
        return f"ガイアの夜明けの処理中にエラーが発生: {e}\n\n{url}"

def get_gulliver_info():
    url = "https://www.tv-tokyo.co.jp/gulliver/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        next_preview_heading = soup.find("h2", class_="tbcms_official-contents__heading", string="次回予告")
        if not next_preview_heading: return "ガリバー: 「次回予告」の見出しが見つかりませんでした。"
        content_block = next_preview_heading.find_parent("div", class_="tbcms_official-contents__block")
        if not content_block: return "ガリバー: コンテンツブロックが見つかりませんでした。"
        paragraphs = content_block.find_all("p")
        valid_paragraphs = [p for p in paragraphs if p.get_text(strip=True)]
        if len(valid_paragraphs) < 2: return "ガリバー: 放送日や詳細情報が見つかりませんでした。"
        date_line = valid_paragraphs[0].get_text(strip=True)
        description = valid_paragraphs[1].get_text(strip=True)
        return f"{date_line}\n{description}\n\n{url}"
    except Exception as e:
        return f"ガリバーの処理中にエラーが発生: {e}\n\n{url}"

# --- 「ブレイクスルー」用の新しい関数 ---
def get_breakthrough_info():
    """
    「ブレイクスルー」用の固定メッセージを返す関数
    """
    url = "https://www.tv-tokyo.co.jp/breakthrough/"
    message = "(土) 10時30分～　※予告が取れないのでリンクのみ"
    return f"{message}\n{url}"

# --- メインの実行部分 ---
if __name__ == "__main__":
    CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
    user_ids_string = os.environ.get('YOUR_USER_ID')

    if not CHANNEL_ACCESS_TOKEN or not user_ids_string:
        print("エラー: 必要な環境変数（アクセストークンまたはユーザーID）が設定されていません。")
        exit()

    user_id_list = user_ids_string.split(',')
    
    # 実行する番組のリスト（ブレイクスルーを追加）
    programs = {
        "WBS": get_wbs_highlights,
        "モーサテ": get_nms_highlights,
        "カンブリア宮殿": get_cambria_info,
        "ガイアの夜明け": get_gaia_info,
        "知られざるガリバー": get_gulliver_info,
        "ブレイクスルー": get_breakthrough_info,
    }
    
    final_message = "今日のテレビ番組情報です！"
    for name, func in programs.items():
        info = func()
        # 出力形式を調整（区切り線の文字数を変更）
        final_message += f"\n\n" + "="*15 + f"\n## {name} ##\n\n{info}"

    # 一斉送信用の関数を呼び出す
    send_line_multicast(final_message, CHANNEL_ACCESS_TOKEN, user_id_list)
    
    print(f"{len(user_id_list)} 人にメッセージが送信されました。")

