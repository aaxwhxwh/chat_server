#!/usr/bin/env python
# -*- coding:utf-8 -*- 
# Date: 2023/2/14
# Name: celery_app.py
# Author: will.xiong
import logging
import traceback
from time import time

import openai
import requests

from config import Config
from server import celery_app

logger = logging.getLogger("root")


class ChatBot:

    def __init__(self, organization, api_key, model, logger):
        openai.organization = organization
        openai.api_key = api_key
        self.model = model
        self.logger = logger

    def prompt(self, prompt_text, temperature=0.3, max_tokens=500, top_p=1.0, frequency_penalty=0.0,
               presence_penalty=0.0):
        try:
            a = time()
            response = openai.Completion.create(
                model=self.model,
                prompt=prompt_text,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                timeout=10
            )
            # print(time()-a)
            # print(prompt_text)
            resp = response['choices'][0]['text'].strip()
            # print('response:',resp)
            self.log(f'''exec time :{time() - a},response:{resp}''')
            return resp
        except Exception as e:
            # print(str(e))
            self.log(traceback.format_exc())
            raise e

    def log(self, msg):
        if self.logger:
            self.logger.info(msg)


chat_bot = ChatBot(organization=Config.OPENAI_ORG, api_key=Config.OPENAI_KEY, model=Config.OPENAI_MODEL, logger=logger)


def get_access_token():

    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={Config.CORP_ID}&corpsecret={Config.CORP_SECRET}"
    resp = requests.get(url)
    return resp.json()["access_token"]


def send_msg(to_user_id, agent_id, text):
    access_token = get_access_token()
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
    data = {
        "touser": to_user_id,
        "msgtype": "text",
        "agentid": agent_id,
        "text": {
            "content": text
        }
    }
    resp = requests.post(url, json=data)


@celery_app.task(bind=True, max_retries=5)
def chat_bot_prompt(self, to_user_id, agent_id, text):
    try:
        resp_content = chat_bot.prompt(text)
    except Exception as e:
        raise self.retry(exc=e, countdown=1)
    if resp_content is None:
        print("获取chat信息异常")
        return
    send_msg(to_user_id, agent_id, resp_content)
