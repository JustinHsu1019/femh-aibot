# from datetime import datetime

from utils.ai.gemini_tem import gemini_template
from utils.ai.gpt_tem import gpt_template


def call_aied(passage, quest, use_gpt: bool):
    # current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    prompt = f"""You are a helpful and informative healthcare bot that answers questions using text from the reference passage included below. \
Be sure to respond in a complete sentence, being comprehensive, including all relevant background information. \
However, you are talking to a non-technical audience, so be sure to break down complicated concepts and \
strike a friendly and conversational tone. \

PASSAGE:
'{passage[0]}

{passage[1]}

{passage[2]}

{passage[3]}

{passage[4]}

[User Question]: '{quest}'

ANSWER:
"""
    try:
        if use_gpt:
            res = gpt_template(prompt)
        else:
            res = gemini_template(prompt)
    except Exception:
        res = '太多使用者請求了！請等待幾秒後再重新詢問'

    return res
