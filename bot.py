"""飞书自建应用机器人常驻服务：长连接(WebSocket)接收消息并存入本地，只记录、永不自动回复。"""
import json
import logging
import os
from datetime import datetime, timezone

# 本机出站经代理时补上 ws/wss 映射（与 qqbot 一致）
if os.environ.get("https_proxy") and not os.environ.get("wss_proxy"):
    os.environ["wss_proxy"] = os.environ["https_proxy"]
if os.environ.get("http_proxy") and not os.environ.get("ws_proxy"):
    os.environ["ws_proxy"] = os.environ["http_proxy"]

import yaml
import lark_oapi as lark
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1

# 本机出站必须走 egress 代理，但 lark_oapi 的 ws 客户端默认强制直连
# （_ws_connect_kwargs 返回 {"proxy": None}），直连会被网关拦截、报
# WRONG_VERSION_NUMBER。改为把环境里的代理地址交给 websockets 走 CONNECT 隧道。
import lark_oapi.ws.client as _lark_ws_client


def _ws_kwargs_via_proxy():
    proxy = os.environ.get("https_proxy") or os.environ.get("http_proxy")
    return {"proxy": proxy} if proxy else {}


_lark_ws_client._ws_connect_kwargs = _ws_kwargs_via_proxy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "app_config.yaml")
STORE_PATH = os.path.join(BASE_DIR, "messages.jsonl")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("feishu-bot")

_PLACEHOLDERS = {"", None, "YOUR_APP_ID", "YOUR_APP_SECRET"}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def append_message(record: dict):
    record["received_at"] = datetime.now(timezone.utc).isoformat()
    with open(STORE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def on_message_receive(data: P2ImMessageReceiveV1) -> None:
    """处理 im.message.receive_v1：提取字段存一行 JSON，不做任何回复。"""
    try:
        event = data.event
        msg = event.message
        sender = event.sender
        msg_type = msg.message_type
        raw_content = msg.content or ""
        if msg_type == "text":
            try:
                text = json.loads(raw_content).get("text", "")
            except (json.JSONDecodeError, AttributeError):
                text = raw_content
        else:
            # 非文本消息保留原始 content JSON
            text = raw_content
        record = {
            "message_id": msg.message_id,
            "chat_id": msg.chat_id,
            "chat_type": msg.chat_type,
            "sender_id": (
                sender.sender_id.open_id
                if sender is not None and sender.sender_id is not None
                else None
            ),
            "msg_type": msg_type,
            "text": text,
            "create_time": msg.create_time,
        }
        logger.info(
            "收到消息 chat_id=%s chat_type=%s from %s: %r",
            record["chat_id"],
            record["chat_type"],
            record["sender_id"],
            text,
        )
        append_message(record)
    except Exception:  # noqa: BLE001
        logger.exception("处理消息事件失败")


def main():
    cfg = load_config()
    app_id = cfg.get("app_id")
    app_secret = cfg.get("app_secret")
    if app_id in _PLACEHOLDERS or app_secret in _PLACEHOLDERS:
        logger.error(
            "app_config.yaml 里 app_id/app_secret 还是占位值，"
            "先在飞书开放平台建自建应用、把真实凭证填进来再启动。"
        )
        raise SystemExit(1)

    handler = (
        lark.EventDispatcherHandler.builder("", "")
        .register_p2_im_message_receive_v1(on_message_receive)
        .build()
    )
    client = lark.ws.Client(
        app_id,
        app_secret,
        event_handler=handler,
        log_level=lark.LogLevel.INFO,
    )
    logger.info("飞书长连接启动（app_id=%s）…", app_id)
    client.start()


if __name__ == "__main__":
    main()
