#!/usr/bin/env python3
"""Send a text message to the user's Feishu group via the custom-bot webhook.
Usage: send.py <message text...>
The bot's keyword security check requires every message to contain the keyword;
it is prepended automatically when missing."""
import json, sys, urllib.request, pathlib

cfg = pathlib.Path(__file__).with_name("config.yaml").read_text()
url = keyword = None
for line in cfg.splitlines():
    if line.startswith("webhook_url:"):
        url = line.split(":", 1)[1].strip()
    elif line.startswith("keyword:"):
        keyword = line.split(":", 1)[1].strip()
if not url:
    sys.exit("webhook_url missing in config.yaml")
text = " ".join(sys.argv[1:]).strip()
if not text:
    sys.exit("empty message")
if keyword and keyword not in text:
    text = keyword + " " + text
data = json.dumps({"msg_type": "text", "content": {"text": text}}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=15) as r:
    print(r.read().decode())
