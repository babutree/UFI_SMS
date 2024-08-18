import os
import re
import json
import logging
import requests
import subprocess
import argparse
from corp_init import Corpid, Agentid, Corpsecret, Touser, Media_id

# 设置日志
logging.basicConfig(filename='sms_log', level=logging.INFO, format='%(asctime)s %(message)s')

# 全局变量
unknow = []
sent = []
recv = []

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
        try:
            req = requests.post(url, params=values)
            req.raise_for_status()
            data = req.json()
            return data["access_token"]
        except requests.RequestException as e:
            logging.error(f"获取access token失败: {e}")
            return None

    def _send_request(self, send_url, send_values):
        send_msges = bytes(json.dumps(send_values), "utf-8")
        try:
            response = requests.post(send_url, send_msges)
            response.raise_for_status()
            return response.json().get("errmsg", "error")
        except requests.RequestException as e:
            logging.error(f"消息发送失败: {e}")
            return str(e)

    def send_text(self, message, touser="@all"):
        access_token = self.get_access_token()
        if not access_token:
            return "error"
        send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
        send_values = {
            "touser": touser,
            "msgtype": "text",
            "agentid": self.AGENTID,
            "text": {"content": message},
            "safe": "0",
        }
        return self._send_request(send_url, send_values)

    def send_mpnews(self, title, message, media_id, touser="@all"):
        access_token = self.get_access_token()
        if not access_token:
            return "error"
        send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
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
        return self._send_request(send_url, send_values)

def wecom_app(title: str, content: str) -> None:
    if not Corpid:
        logging.error("corp_init.py 未设置!!\n取消推送")
        return "error"
    
    wx = WeCom(Corpid, Corpsecret, Agentid)
    if not Media_id:
        message = title + "\n" + content
        response = wx.send_text(message, Touser)
    else:
        response = wx.send_mpnews(title, content, Media_id, Touser)

    if response == "ok":
        logging.info("企业微信推送成功")
    else:
        logging.error(f"企业微信推送失败：{response}")
    return response

def get_msg_num(line):
    return int(line.rstrip(' (sent)\n').rstrip(' (received)\n').rstrip(' (unknown)\n')[::-1].split('/', 1)[0])

def send_msg(num):
    os.system(f"sudo mmcli -s {num} --send")

def del_msg(num):
    os.system(f"sudo mmcli -m 0 --messaging-delete-sms={num}")

def scan_local_msg():
    result = subprocess.run(['mmcli', '-m', '0', '--messaging-list-sms'], stdout=subprocess.PIPE, text=True)
    for line in result.stdout.splitlines():
        if line.endswith(' (unknown)\n'):
            unknow.append(get_msg_num(line))
        elif line.endswith(' (sent)\n'):
            sent.append(get_msg_num(line))
        elif line.endswith(' (received)\n'):
            recv.append(get_msg_num(line))
    logging.info(f"未发送：{unknow} 已发送：{sent} 接收：{recv}")

def add_msg(number, text):
    os.system(f"sudo mmcli -m 0 --messaging-create-sms=\"text='{text}',number='+{number}'\"")

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
    for i in recv:
        result = subprocess.run(['mmcli', '-m', '0', '-s', str(i)], stdout=subprocess.PIPE, text=True)
        sms = re.sub(r'\s|\t|\n|-', '', result.stdout)
        number = sms[sms.find('number:') + 7:sms.find('|text')]
        text = sms[sms.find('text:') + 5:sms.find('Properties|')]
        time = sms[sms.find('timestamp:') + 10:sms.find('timestamp:') + 27].replace('T', ' - ')

        response = wecom_app(f"{number}\n", f"{text}\n\n{time}")

        if response == "ok":
            del_msg(i)

def parse_arguments():
    parser = argparse.ArgumentParser(description="随身wifi短信转发工具")
    parser.add_argument('command', choices=['add', 'send', 'clean', 'forward'], help="要执行的操作")
    parser.add_argument('number', nargs='?', help="接收者号码 (仅对 'add' 命令有效)")
    parser.add_argument('text', nargs='?', help="短信内容 (仅对 'add' 命令有效)")
    return parser.parse_args()

def main():
    args = parse_arguments()

    if args.command == 'add':
        if not args.number or not args.text:
            logging.error("add命令需要接收者号码和短信内容")
        else:
            add_msg(args.number, args.text)
    elif args.command == 'send':
        scan_local_msg()
        send_all()
    elif args.command == 'clean':
        scan_local_msg()
        clean_sent()
        clean_unknow()
        clean_recv()
    elif args.command == 'forward':
        scan_local_msg()
        forward_msg()
    else:
        logging.error("未知命令")

if __name__ == "__main__":
    main()
