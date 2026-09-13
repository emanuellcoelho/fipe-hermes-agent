#!/usr/bin/env python3
"""post_chat.py -- one message to the owner's home channel. Or nothing.

The sweep's chat leg. A quiet sweep posts NOTHING: this only runs when the
model decided there is something to say, and it says it with this.

Usage:
    post_chat.py --file <path>      the message body, read whole from a file
    post_chat.py --text <string>    the message body, inline
    post_chat.py --dry-run ...      print the plan, post nothing

The Plow names come from the process environment -- first boot publishes them
from the credential the host dropped in, and a cron turn inherits them from
the gateway. A missing or blank name refuses BEFORE anything is sent, so a
half-configured turn can never post half a message.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request


def require(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value:
        sys.exit(
            f"{name} is unset or blank in this process's environment -- first "
            "boot publishes it there from the credential the host dropped in; "
            "refusing before anything is sent"
        )
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    body = parser.add_mutually_exclusive_group(required=True)
    body.add_argument("--file", help="read the message body from this file")
    body.add_argument("--text", help="the message body, inline")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    text = open(args.file, encoding="utf-8").read() if args.file else args.text
    if not text or not text.strip():
        sys.exit("empty message body -- nothing to post")

    base = require("PLOW_API_BASE").rstrip("/")
    uid = require("PLOW_HOME_CHANNEL")
    token = require("PLOW_AGENT_TOKEN")
    url = f"{base}/v1/chats/{uid}/messages"
    payload = json.dumps({"body": text}).encode()

    if args.dry_run:
        print(f"dry-run: POST {len(payload)} bytes to {url} (bearer withheld)")
        return 0

    request = urllib.request.Request(
        url, data=payload, method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status // 100 != 2:
            sys.exit(f"chat send answered HTTP {response.status}")
    print(f"posted ({len(text)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
