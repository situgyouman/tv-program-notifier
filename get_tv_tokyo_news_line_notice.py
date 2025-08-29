import requests
import json
import os # GitHub Actionsで秘密情報を読み込むために追加
from bs4 import BeautifulSoup

# --- 通知を送る関数 (Messaging API用) ---
def send_line_message(message, channel_access_token, user_id):
    """
    LINE Messaging APIを使ってプッシュメッセージを送信する関数
    """
    line_api_url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {channel_access_token}'
    }
    payload = {
        'to': user_id,
        'messages': [{'type': 'text', 'text': message}]
    }
    requests.post(line_api_url, headers=headers, data=json.dumps(payload))

# --- 各番組の情報を取得する関数 ---

def get_wbs_highlights():
    """
    テレビ東京 WBSの公式サイトから「番組の見どころ」を取得する関数
    """
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
        return f"--- {title} ---\n{date}\n{text}"
    except Exception as e:
        return f"WBSの処理中にエラーが発生: {e}"

def get_nms_highlights():
    """
    テレビ東京 モーサテの公式サイトから「番組の見どころ」を取得する関数
    """
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
        return f"--- {title} ---\n{date}\n{text}"
    except Exception as e:
        return f"モーサテの処理中にエラーが発生: {e}"

def get_cambria_info():
    """
    「カンブリア宮殿」公式サイトから次回の放送情報を取得する関数
    """
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
        return f"次回のカンブリア宮殿は {date}\n{title}"
    except Exception as e:
        return f"カンブリア宮殿の処理中にエラーが発生: {e}"

def get_gaia_info():
    """
    「ガイアの夜明け」公式サイトから次回の放送情報を取得する関数
    """
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
        return f"{date}\n{title}"
    except Exception as e:
        return f"ガイアの夜明けの処理中にエラーが発生: {e}"

def get_gulliver_info():
    """
    「知られざるガリバー」公式サイトから次回の放送情報を取得する関数
    """
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
        return f"{date_line}\n{description}"
    except Exception as e:
        return f"ガリバーの処理中にエラーが発生: {e}"

# --- メインの実行部分 (GitHub Actions対応版) ---
if __name__ == "__main__":
    # GitHub ActionsのSecretsから情報を安全に読み込む
    CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
    YOUR_USER_ID = os.environ.get('YOUR_USER_ID')

    # 実行に必要な情報が設定されているか確認
    if not CHANNEL_ACCESS_TOKEN or not YOUR_USER_ID:
        print("エラー: 必要な環境変数（アクセストークンまたはユーザーID）が設定されていません。")
        exit() # 情報がなければプログラムを終了

    # 指定の順番にリストを定義
    programs = {
        "WBS": get_wbs_highlights,
        "モーサテ": get_nms_highlights,
        "カンブリア宮殿": get_cambria_info,
        "ガイアの夜明け": get_gaia_info,
        "知られざるガリバー": get_gulliver_info,
    }
    
    # LINEで送るメッセージを作成
    final_message = "今日のテレビ番組情報です！"
    for name, func in programs.items():
        info = func()
        final_message += f"\n\n" + "="*15 + f"\n## {name} ##\n" + info

    # 新しい関数を使って結果をLINEに送信
    send_line_message(final_message, CHANNEL_ACCESS_TOKEN, YOUR_USER_ID)
    
    # 実行確認のため、コンソールにも表示
    print("メッセージがLINEに送信されました。")