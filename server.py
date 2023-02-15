import logging
from logging.config import dictConfig
from xml.etree import cElementTree as ET

from celery import Celery
from flask import Flask, request, Response

from WXBizMsgCrypt3 import WXBizMsgCrypt
from config import Config

app = Flask(__name__)
dictConfig(Config.LOG_PATTERN)
app.config.from_object(Config)

celery_app = Celery("tasks", broker=Config.REDIS_URL)
celery_app.conf.update(app.config)

logger = logging.getLogger(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/work/callback", methods=["GET", "POST"])
def work_callback():

    wx_cpt = WXBizMsgCrypt(Config.TOKEN, Config.ENCODING_AES_KEY, Config.CORP_ID)
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
        to_user_id = xml_tree.find("FromUserName").text
        agent_id = xml_tree.find("AgentID").text
        from celery_tasks import chat_bot_prompt
        chat_bot_prompt.delay(to_user_id, agent_id, content)
        return Response()
