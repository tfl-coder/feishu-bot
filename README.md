# feishu-bot · Yuki 的飞书伴学机器人

飞书自建应用双向机器人：长连接接收群消息、向「muse伴学」群推送学习与作息监督内容（晨间打卡卡、22:30 睡前提醒、周日结算），并能回读群历史（手机屏幕日报的数据入口）。

## 组件

| 文件 | 作用 |
|---|---|
| `bot.py` | 长连接接收端（lark-oapi WebSocket），把群消息落盘到 `messages.jsonl` |
| `bin/feishu` | 发送/回读 CLI：`send` 支持文本、富文本 post、图片、文件、卡片五种消息；`history` 回读群历史（含应用自发消息） |
| `send.py` | 群自定义机器人 webhook 备份发送通道（关键词校验） |
| `feishu-bot.service` | systemd 单元（Restart=always） |
| `systemd/install.sh` | 看门狗：幂等安装/拉起服务 |

## 部署

1. 复制 `app_config.example.yaml` 为 `app_config.yaml`，填入飞书开放平台自建应用的 App ID / App Secret；如需 webhook 备份通道，再复制 `config.example.yaml` 为 `config.yaml`。真实配置文件权限 600，且已被 `.gitignore` 排除。
2. 建 Python 虚拟环境并装 `lark-oapi`（出站需走环境里的 egress 代理，bot.py 已处理）。
3. `systemd/install.sh` 安装并启动服务。
4. 应用需开通权限：`im:message:send_as_bot`、`im:resource:upload` 等。

## 约定

- 消息回复走事件驱动：零 token 的小脚本盯 `messages.jsonl`，有新消息才唤醒 agent 回复，不做定时轮询。
- 屏幕使用数据由配套安卓应用「Yuki屏幕日报」（独立仓库 yuki-usage-app）每晚发进群，本机器人负责回读记账。
