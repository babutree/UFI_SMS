import os
import sys
import re
import json
import logging
import requests
from datetime import datetime, timedelta
from corp_init import Corpid, Agentid, Corpsecret, Touser, Media_id

# 初始化日志记录
logging.basicConfig(
    filename='/home/UFI_WeCom_SMS_Forwarder/sms_log',
    level=logging.INFO,
    format='%(message)s'
)

# 短信缓存，用于防止重复发送
last_sms = {"text": "", "time": datetime.now()}

# 保存日志
def save_log(title, content):
    logging.info(f"{content}\n{title}")

# 企业微信APP推送消息
def wecom_app(title: str, content: str) -> None:
    if not Corpid:
        logging.error("corp_init.py 未设置!!\n取消推送")
        return "error"
    
    wx = WeCom(Corpid, Corpsecret, Agentid)
    
    recipient = Touser
    
    if not Media_id:
        message = title + "\n" + content
        response = wx.send_text(message, recipient)
    else:
        response = wx.send_mpnews(title, content, Media_id, recipient)

    if response == "ok":
        logging.info("企业微信APP推送成功")
    else:
        logging.error(f"推送失败：{response}")
    return response

class WeCom:
    def __init__(self, corpid, corpsecret, agentid):
        self.CORPID = corpid
        self.CORPSECRET = corpsecret
        self.AGENTID = agentid

    def get_access_token(self):
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        values = {
            "corpid": self.CORPID,
            "corpsecret": self.CORPSECRET,
        }
        req = requests.post(url, params=values)
        data = json.loads(req.text)
        return data["access_token"]

    def send_text(self, message, touser):
        send_url = (
            "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token="
            + self.get_access_token()
        )
        send_values = {
            "touser": touser,
            "msgtype": "text",
            "agentid": self.AGENTID,
            "text": {"content": message},
            "safe": "0",
        }
        send_msges = bytes(json.dumps(send_values), "utf-8")
        response = requests.post(send_url, send_msges)
        return response.json().get("errmsg", "error")

    def send_mpnews(self, title, message, media_id, touser):
        send_url = (
            "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token="
            + self.get_access_token()
        )
        send_values = {
            "touser": touser,
            "msgtype": "mpnews",
            "agentid": self.AGENTID,
            "mpnews": {
                "articles": [
                    {
                        "title": title,
                        "thumb_media_id": media_id,
                        "author": "Author",
                        "content_source_url": "",
                        "content": message.replace("\n", "<br/>"),
                        "digest": message,
                    }
                ]
            },
        }
        send_msges = bytes(json.dumps(send_values), "utf-8")
        response = requests.post(send_url, send_msges)
        return response.json().get("errmsg", "error")

def get_msg_num(line):
    return int(line.rstrip(' (sent)\n').rstrip(' (received)\n').rstrip(' (unknown)\n')[::-1].split('/',1)[0])

def send_msg(num):
    os.system("sudo mmcli -s "+str(num)+" --send")

def del_msg(num):
    os.system("sudo mmcli -m 0 --messaging-delete-sms="+str(num))

def scan_local_msg():
    p=os.popen('mmcli -m 0 --messaging-list-sms') 
    for line in p.readlines():
        if line.endswith(' (unknown)\n'):
            num = get_msg_num(line)
            unknow.append(num)
        if line.endswith(' (sent)\n'):
            num = get_msg_num(line)
            sent.append(num)
        if line.endswith(' (received)\n'):
            num = get_msg_num(line)
            recv.append(num)    
    print('未发送：', unknow, '已发送：', sent, '接收：', recv)

def add_msg(number, text):
    os.system("sudo mmcli -m 0 --messaging-create-sms=\"text=\'"+text+"\',number=\'+"+number+"\'\"")

def clean_sent():
    for i in sent:
        del_msg(i)
        
def clean_unknow():
    for i in unknow:
        del_msg(i)
        
def clean_recv():
    for i in recv:
        del_msg(i)

def send_all():
    for i in unknow:
        send_msg(i)

def forward_msg():
    global last_sms
    
    for i in recv:
        p = os.popen('mmcli -m 0 -s ' + str(i))
        sms = re.sub('\s|\t|\n|-','',p.read())
        
        number = sms[sms.find('number:') + 7:sms.find('|text')]
        text = sms[sms.find('text:') + 5:sms.find('Properties|')]
        time = sms[sms.find('timestamp:') + 10:sms.find('timestamp:') + 27].replace('T', ' - ')
        
        current_time = datetime.now()
        
        if text != last_sms["text"] or (current_time - last_sms["time"]).seconds > 60:
            response = wecom_app(text, f"{number}\nUFI-{time}")
            if response == "ok":
                save_log(text, f"{number}\nUFI-{time}")
                del_msg(i)
                last_sms = {"text": text, "time": current_time}

cmd = sys.argv
cmd_len = len(cmd)
try:
    if cmd[1] == 'add':
        add_msg(cmd[2], cmd[3])
    elif cmd[1] == 'send':
        scan_local_msg()
        send_all()
    elif cmd[1] == 'clean':
        scan_local_msg()
        clean_sent()
        clean_unknow()
        clean_recv()
    elif cmd[1] == 'forward':
        scan_local_msg()
        forward_msg()
    else:
        pass
except IndexError:
    pass
