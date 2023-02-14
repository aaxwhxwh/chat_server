import logging
import traceback
from time import time
from xml.etree import cElementTree as ET

import openai
from flask import Flask, request, Response

from WXBizMsgCrypt3 import WXBizMsgCrypt

app = Flask(__name__)

logger = logging.getLogger(__name__)
class ChatBot:

    def __init__(self,organization,api_key,model,logger):
        openai.organization = organization
        openai.api_key = api_key
        self.model = model
        self.logger = logger

    def prompt(self,prompt_text,temperature=0.3,max_tokens=500,top_p=1.0,frequency_penalty=0.0,presence_penalty=0.0):
        try:
            a = time()
            response = openai.Completion.create(
                model=self.model,
                prompt=prompt_text,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty
            )
            # print(time()-a)
            # print(prompt_text)
            resp = response['choices'][0]['text'].strip()
            # print('response:',resp)
            self.log(f'''exec time :{time()-a},response:{resp}''')
            return resp
        except Exception as e:
            self.log(traceback.format_exc())

    def log(self,msg):
        if self.logger:
            self.logger.info(msg)

# openai参数
OPENAI_ORG = 'org-cJOuskbI6DaXGptChpPsv5oA'
OPENAI_KEY = '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'
OPENAI_MODEL = 'text-davinci-003' # text-ada-001 text-davinci-003

chat_bot = ChatBot(organization=OPENAI_ORG,api_key=OPENAI_KEY,model=OPENAI_MODEL,logger=logger)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/work/callback", methods=["GET", "POST"])
def work_callback():
    s_token = "Y4MIckdILg2V5miRXdU6sXaGze"
    s_encoding_aes_key = "JRBg8M2glfrkxeCdU9jLzQTskGMA0azJbt9gnHKFIBz"
    s_corp_id = "ww82cdb93a71a35c21"
    wx_cpt = WXBizMsgCrypt(s_token, s_encoding_aes_key, s_corp_id)
    if request.method == "GET":
        params = request.args
        echo_str = params["echostr"]
        msg_signature = params["msg_signature"]
        nonce = params["nonce"]
        timestamp = params["timestamp"]
        ret, echo_str = wx_cpt.VerifyURL(msg_signature, timestamp, nonce, echo_str)
        return echo_str
    elif request.method == "POST":
        params = request.args
        data = request.data
        if isinstance(data, str):
            import json
            data = json.loads(data)
        signature = params.get("msg_signature")
        timestamp = params.get("timestamp")
        nonce = params.get("nonce")
        ret, s_msg = wx_cpt.DecryptMsg(data, signature, timestamp, nonce)
        xml_tree = ET.fromstring(s_msg)
        content = xml_tree.find("Content").text
        to_user_name = xml_tree.find("ToUserName").text
        agent_id = xml_tree.find("AgentID").text
        resp_content = chat_bot.prompt(content)
        from time import time
        create_time = int(time())
        s_resp_data = f"<xml><ToUserName>{to_user_name}</ToUserName><FromUserName>ChenJiaShun</FromUserName><CreateTime>{create_time}</CreateTime><MsgType>text</MsgType><Content>{resp_content}</Content><MsgId>1456453720</MsgId><AgentID>{agent_id}</AgentID></xml>"
        ret, s_encrypt_msg = wx_cpt.EncryptMsg(s_resp_data, nonce, create_time)
        return Response(s_encrypt_msg)
