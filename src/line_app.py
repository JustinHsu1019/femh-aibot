from flask import Flask, request, jsonify
import requests
import os
import uuid

app = Flask(__name__)

# 定義存放來源檔案的目錄
TEMP_STORAGE_DIR = "temp_storage"
os.makedirs(TEMP_STORAGE_DIR, exist_ok=True)

@app.route('/line_webhook', methods=['POST'])
def line_webhook():
    # 從 LINE 收到的輸入
    user_data = request.get_json()
    user_input = user_data.get("message", "")

    # 模擬請求後端聊天 API
    api_url = "http://127.0.0.1:5001/api/chat"
    payload = {"message": user_input}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response_data = response.json()
    except Exception as e:
        return jsonify({"error": f"API error: {e}"}), 500

    # 提取返回資料
    llm_output = response_data.get("llm", "無法取得回應")
    retriv_output = response_data.get("retriv", "[]")

    # 創建臨時連結
    retriv_links = create_temp_links(retriv_output)

    # 返回結果
    result = {
        "llm": llm_output,
        "source_links": retriv_links,
    }
    return jsonify(result)


@app.route('/retriv/<unique_id>', methods=['GET'])
def retriv_content(unique_id):
    """
    提供 retriv 的檔案內容
    """
    file_path = os.path.join(TEMP_STORAGE_DIR, f"{unique_id}.txt")
    if not os.path.exists(file_path):
        return "Content not found", 404

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return f"<h1>Source Content</h1><p>{content}</p>"


def create_temp_links(retriv_output):
    """
    將 retriv 資料存成檔案並創建超連結
    """
    import json
    try:
        retriv_items = json.loads(retriv_output.replace("'", '"'))  # 確保格式正確
    except Exception as e:
        return f"Invalid retriv format: {e}"

    links = []
    for item in retriv_items:
        title = item.get("title", "No Title")
        content = item.get("content", "No Content")

        # 生成唯一檔案名稱
        unique_id = str(uuid.uuid4())
        file_path = os.path.join(TEMP_STORAGE_DIR, f"{unique_id}.txt")

        # 將內容存成檔案
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 創建臨時 URL
        link = f"<a href='/retriv/{unique_id}' target='_blank'>{title}</a>"
        links.append(link)

    # 返回 HTML 格式的連結
    return "<br>".join(links)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
