#!/usr/bin/env bash
# 幂等安装/修复 feishu-bot systemd 服务（供事件看门狗调用）
set -euo pipefail
UNIT_SRC="/home/hatch/workspace/feishu/feishu-bot.service"
UNIT_DST="/etc/systemd/system/feishu-bot.service"

if [ ! -f "$UNIT_DST" ] || ! cmp -s "$UNIT_SRC" "$UNIT_DST"; then
  cp "$UNIT_SRC" "$UNIT_DST"
  systemctl daemon-reload
  systemctl enable feishu-bot.service >/dev/null 2>&1 || true
fi

if ! systemctl is-active --quiet feishu-bot.service; then
  systemctl start feishu-bot.service
fi
