#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

"""
WeCom 配置文件

该文件包含用于企业微信 API 交互的基本配置。
请确保填写正确的企业ID、应用ID、密钥和目标用户。

字段说明:
    Corpid: 企业ID（必填）
    Agentid: 企业应用的ID（必填）
    Corpsecret: 企业应用的凭证密钥（必填）
    Touser: 成员ID（可选，默认@all，多个成员ID使用 '|' 隔开）
    Media_id: 媒体文件ID（可选，不填则发送文本信息）

企业微信开发者文档: https://developer.work.weixin.qq.com/document/path/90236
"""

Corpid = ""  # 必填：请填写你的企业ID
Agentid = ""  # 必填：请填写你的企业应用ID
Corpsecret = ""  # 必填：请填写你的企业应用凭证密钥
Touser = ""  # 必填：默认为@all，发送给所有成员
Media_id = ""  # 可选：媒体文件ID，不填则默认发送文本消息
