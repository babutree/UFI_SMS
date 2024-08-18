
# 基于以下项目魔改而来：
SMS_Forward https://github.com/n0raml/SMS-Forward

ufi-message https://gitee.com/jiu-xiao/ufi-message

ufi_sms https://github.com/Angels-Ray/ufi_sms

# UFI WeCom SMS Forwarder
## 项目简介

UFI WeCom SMS Forwarder 是一个基于 Python 的工具，设计用于自动转发已安装Debian的随身Wi-Fi设备（UFI）接收到的短信到企业微信（WeCom）自建应用。通过这个工具，用户可以方便地将设备上的短信实时转发给企业微信应用中的指定成员，便于集中管理和及时处理短信内容。

## 依赖项

在使用本项目之前，请确保安装以下依赖项：

Python 3

requests 库（用于处理 HTTP 请求）

cron（用于设置定时任务）

依赖项安装示例：

    apt update
    apt install python3 python3-pip cron
    pip3 install requests

# 配置指南
## 配置企业微信信息

在使用短信转发功能之前，必须先配置 corp_init.py 文件，填入企业微信的相关信息：

    Corpid = "your_corpid"  # 替换为你的企业ID
    Agentid = "your_agentid"  # 替换为你的企业应用ID
    Corpsecret = "your_corpsecret"  # 替换为你的企业应用凭证密钥
    Touser = "@all"  # 默认为 @all，发送给所有成员
    Media_id = ""  # 可选：媒体文件ID，不填则发送文本消息

# 功能说明

## 将指定内容的短信添加到暂存区，稍后可以发送。

    python3 msg.py add 861234567890 "text"

此命令将内容为 "text" 的短信添加到号码 861234567890 的暂存区中。

## 将暂存区中所有待发送的短信立即发送出去。

    python3 msg.py send

## 删除本地存储的所有短信，包括暂存的、已发送的和接收的短信。

    python3 msg.py clean

## 通过企业微信将接收到的短信内容转发给指定成员。

    python3 msg.py forward

## 日志记录

所有成功发送的短信会记录在当前目录下的 sms_log 文件中。用户可以通过查看该文件获取发送记录。如果不需要记录日志，可以注释掉 msg.py 中的以下代码行：

    save_log(title, content)

## 短信自动删除

默认情况下，成功发送的短信会从设备中自动删除。如果不想删除这些短信，可以注释掉 msg.py 中的以下代码行：

    del_msg(i)

# 配置定时任务

可以通过 cron 来设置定时任务，以每分钟自动检查并转发新收到的短信。

## 安装 cron（如果未安装）：

    apt install cron

## 配置 cron 任务：

    crontab -e

添加以下内容，使其每分钟查询一次新短信并转发：

    */1 * * * * python3 /home/user/UFI_WeCom_SMS_Forwarder/msg.py forward

请将/home/user修改为脚本所在目录

每分钟运行该任务，它会检查设备上是否有新收到的短信，并将未转发的短信内容推送到 WeCom应用。如果没有新短信，脚本会退出，不会进行推送。

保存并退出后，cron 将每分钟执行一次短信转发任务。

# 许可证

本项目基于一个未声明开源许可证的上游项目进行修改和扩展。由于上游项目没有明确的许可证声明，请在使用和分发本项目时谨慎。如果你计划在商业项目中使用，请先联系上游作者以获取相关许可。

# 贡献

如果你有任何改进建议或发现问题，欢迎通过 GitHub 提交 issue 或 pull request 来贡献你的代码。
