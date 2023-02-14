from flask import Flask, request

from xml.etree import cElementTree as ET
from WXBizMsgCrypt3 import WXBizMsgCrypt

app = Flask(__name__)


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
        print(data)
        print(type(data))
        if isinstance(data, str):
            import json
            data = json.loads(data)
        signature = params.get("signature")
        timestamp = params.get("timestamp")
        nonce = params.get("nonce")
        ret, s_msg = wx_cpt.DecryptMsg(data, signature, timestamp, nonce)
        xml_tree = ET.fromstring(s_msg)
        content = xml_tree.find("Content").text
        to_user_name = xml_tree.find("ToUserName").text
        agent_id = xml_tree.find("AgentID").text
        print(content)
        from time import time
        create_time = int(time())
        s_resp_data = f"<xml><ToUserName>{to_user_name}</ToUserName><FromUserName>ChenJiaShun</FromUserName><CreateTime>{create_time}</CreateTime><MsgType>text</MsgType><Content>你好</Content><MsgId>1456453720</MsgId><AgentID>{agent_id}</AgentID></xml>"
        ret, s_encrypt_msg = wx_cpt.EncryptMsg(s_resp_data, nonce, create_time)
        return s_encrypt_msg
