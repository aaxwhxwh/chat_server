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
from celery import Celery

logger = logging.getLogger(__name__)

celery_app = Celery("tasks", broker="redis://127.0.0.1:6379/1")


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
                presence_penalty=presence_penalty
            )
            # print(time()-a)
            # print(prompt_text)
            resp = response['choices'][0]['text'].strip()
            # print('response:',resp)
            self.log(f'''exec time :{time() - a},response:{resp}''')
            return resp
        except Exception as e:
            print(str(e))
            self.log(traceback.format_exc())

    def log(self, msg):
        if self.logger:
            self.logger.info(msg)


# openai参数
OPENAI_ORG = ''
OPENAI_KEY = ""
OPENAI_MODEL = ''  # text-ada-001 text-davinci-003

chat_bot = ChatBot(organization=OPENAI_ORG, api_key=OPENAI_KEY, model=OPENAI_MODEL, logger=logger)




def get_access_token():
    corp_id = ""
    corp_secret = ""
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corp_id}&corpsecret={corp_secret}"
    resp = requests.get(url)
    print(resp.status_code)
    print(resp.json())
    return resp.json()["access_token"]


def send_msg(to_user_id, text):
    access_token = get_access_token()
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
    data = {
       "touser" : to_user_id,
       "msgtype" : "text",
       "agentid" : 1000006,
       "text" : {
           "content" : text
       },
       # "safe":0,
       # "enable_id_trans": 0,
       # "enable_duplicate_check": 0,
       # "duplicate_check_interval": 1800
    }
    resp = requests.post(url, json=data)


@celery_app.task
def chat_bot_prompt(to_user_id, text):
    resp_content = chat_bot.prompt(text)
    send_msg(to_user_id, resp_content)