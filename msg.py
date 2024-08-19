import os
import sys
import re
import json
import requests
import hashlib
import time
from corp_init import Corpid, Agentid, Corpsecret, Touser, Media_id

log_dir = '/home/UFI_WeCom_SMS_Forwarder/'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, 'sms_log')
sent_messages = {}

unknow = []
sent = []
recv = []

# 保存日志到指定文件中
def save_log(title, content):
    with open(log_file, 'a+', errors='ignore') as oldrss:
        oldrss.write(f"{title} - {content}\n")

# 生成内容的哈希值用于重复检测
def generate_hash(content):
    cleaned_content = re.sub(r'\s+', '', content)
    return hashlib.md5(cleaned_content.encode('utf-8')).hexdigest()

# 企业微信APP推送功能
def wecom_app(title: str, content: str, touser: str = Touser) -> str:
    if not Corpid:
        print("corp_init.py 未设置!!\n取消推送")
        return "error"

    print("企业微信APP推送服务启动")
    wx = WeCom(Corpid, Corpsecret, Agentid)
    if not Media_id:
        message = f"{title}\n{content}"
        response = wx.send_text(message, touser)
    else:
        response = wx.send_mpnews(title, content, Media_id, touser)

    if response == "ok":
        print("企业微信APP推送成功！")
        save_log(title, content)
    else:
        print(f"推送失败！错误信息如下：\n{response}")
    return response

# 企业微信APP相关配置和发送方法
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
        data = req.json()
        return data["access_token"]

    def send_text(self, message, touser="@all"):
        send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.get_access_token()}"
        send_values = {
            "touser": touser,
            "msgtype": "text",
            "agentid": self.AGENTID,
            "text": {"content": message},
            "safe": "0",
        }
        send_msges = bytes(json.dumps(send_values), "utf-8")
        respone = requests.post(send_url, send_msges)
        respone = respone.json()
        return respone["errmsg"]

    def send_mpnews(self, title, message, media_id, touser="@all"):
        send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.get_access_token()}"
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
        respone = requests.post(send_url, send_msges)
        respone = respone.json()
        return respone["errmsg"]

# 获取短信编号
def get_msg_num(line):
    return int(line.rstrip(' (sent)\n').rstrip(' (received)\n').rstrip(' (unknown)\n')[::-1].split('/', 1)[0])

# 发送短信
def send_msg(num):
    os.system(f"sudo mmcli -s {num} --send")

# 删除短信
def del_msg(num):
    os.system(f"sudo mmcli -m 0 --messaging-delete-sms={num}")

# 扫描本地短信
def scan_local_msg():
    p = os.popen('mmcli -m 0 --messaging-list-sms')
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

# 添加短信到暂存区
def add_msg(number, text):
    os.system(f"sudo mmcli -m 0 --messaging-create-sms=\"text='{text}',number='+{number}'\"")

# 清理已发送短信
def clean_sent():
    for i in sent:
        del_msg(i)

# 清理未发送短信
def clean_unknow():
    for i in unknow:
        del_msg(i)

# 清理接收的短信
def clean_recv():
    for i in recv:
        del_msg(i)

# 发送所有未发送短信
def send_all():
    for i in unknow:
        send_msg(i)

# 检测是否为重复短信
def is_duplicate(content):
    message_hash = generate_hash(content)
    current_time = time.time()

    if message_hash in sent_messages:
        last_sent_time = sent_messages[message_hash]
        if current_time - last_sent_time < 60:  # 60秒重复检测
            print(f"检测到重复短信，60秒内不发送: {content}")
            save_log("重复短信检测", content)
            return True

    sent_messages[message_hash] = current_time
    return False

# 转发接收的短信
def forward_msg():
    for i in recv:
        p = os.popen(f'mmcli -m 0 -s {i}')
        sms = re.sub(r'\s|\t|\n|-', '', p.read())
        number = sms[sms.find('number:') + 7:sms.find('|text')]
        text = sms[sms.find('text:') + 5:sms.find('Properties|')]
        time_stamp = sms[sms.find('timestamp:') + 10:sms.find('timestamp:') + 27].replace('T', ' - ')

        content = f"{text}\n{number}\nUFI-{time_stamp}"

        if not is_duplicate(content):
            response = wecom_app(f"{text}\n", content, touser=Touser)
            if response == "ok":
                del_msg(i)

cmd = sys.argv
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
        print("Invalid command")
except IndexError:
    print("Invalid command")
