from flask import Flask, request, jsonify
import requests
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError

import utils.config_log as config_log

config, logger, CONFIG_PATH = config_log.setup_config_and_logging()
config.read(CONFIG_PATH)

app = Flask(__name__)

# LINE Channel Access Token and Channel Secret
LINE_CHANNEL_ACCESS_TOKEN = config.get('Line', 'channel_access_token')
LINE_CHANNEL_SECRET = config.get('Line', 'secret')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# API Endpoint to query the LLM
API_URL = "http://34.81.110.126:5000/api/chat"

@app.route("/callback", methods=['POST'])
def callback():
    # Get request headers and body
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text  # User's message from LINE

    # Prepare payload for the external API
    payload = {"message": user_input}
    headers = {"Content-Type": "application/json"}

    try:
        # Send request to the external API
        response = requests.post(API_URL, json=payload, headers=headers)
        response_data = response.json()

        # Extract the llm_output
        llm_output = response_data.get("llm", "無法取得回應")

        # Send the llm_output back to the user on LINE
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=llm_output)
        )
    except Exception as e:
        # Handle any exceptions and send an error message
        error_message = f"發生錯誤: {str(e)}"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=error_message)
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
