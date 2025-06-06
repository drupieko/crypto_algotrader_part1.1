#!/usr/bin/env python3
"""
news_filter_notify.py

Loop every 5 seconds, check raw_news_queue for new articles.
If weight >= min_weight OR keyword matches, batch them and send
to Telegram without exceeding rate limits.
"""

import time
import sqlite3
import yaml
import requests
from datetime import datetime, timezone
import os

# Paths
BASE_DIR = "/home/tito/crypto_algotrader_part1/part1"
DB_PATH = os.path.join(BASE_DIR, "db/crypto.db")
FILTER_CFG_PATH = os.path.join(BASE_DIR, "config/news_filter_config.yaml")
TELEGRAM_CFG_PATH = os.path.join(BASE_DIR, "config/telegram_config.yaml")

CHECK_INTERVAL = 5  # seconds
BATCH_SIZE = 5
RATE_LIMIT_SECONDS = 3.2  # Wait at least this long between messages

# Load config
with open(FILTER_CFG_PATH, "r") as f:
    cfg = yaml.safe_load(f)
KEYWORDS = [kw.lower() for kw in cfg.get("keywords", [])]
MIN_WEIGHT = cfg.get("min_weight", 2)

with open(TELEGRAM_CFG_PATH, "r") as f:
    tcfg = yaml.safe_load(f)
BOT_TOKEN = tcfg["bot_token"]
CHAT_ID = tcfg["chat_id"]
PARSE_MODE = tcfg.get("parse_mode", "Markdown")
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

last_sent_time = 0

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def notify_telegram(text: str):
    global last_sent_time

    now = time.time()
    wait_time = last_sent_time + RATE_LIMIT_SECONDS - now
    if wait_time > 0:
        time.sleep(wait_time)

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": PARSE_MODE
    }
    try:
        resp = requests.post(TELEGRAM_URL, json=payload, timeout=5)
        resp.raise_for_status()
        last_sent_time = time.time()
        return True
    except Exception as e:
        now_ts = datetime.now(timezone.utc).isoformat()
        print(f"[{now_ts}] ERROR sending Telegram: {e}")
        return False

def format_article(row):
    title = row["title"] or ""
    summary = row["summary"] or ""
    weight = row["weight"]
    link = row["link"]
    published = row["published_at"]

    keyword_match = any(kw in title.lower() or kw in summary.lower() for kw in KEYWORDS)
    match_text = "_Keyword match: yes_\n" if keyword_match else ""

    return (
        f"*{title.strip()}*\n"
        f"Published: {published}\n"
        f"Weight: {weight} source{'s' if weight > 1 else ''}\n"
        f"{match_text}"
        f"[Read more]({link})"
    )

def main_loop():
    conn = get_db_connection()
    cursor = conn.cursor()

    while True:
        # Get unalerted articles
        cursor.execute("""
          SELECT r.*
          FROM raw_news_queue r
          LEFT JOIN alerted_articles a
            ON r.article_id = a.article_id
          WHERE a.article_id IS NULL
        """)
        new_articles = cursor.fetchall()

        batch = []
        batch_ids = []

        for row in new_articles:
            aid = row["article_id"]
            title = row["title"] or ""
            summary = row["summary"] or ""
            weight = row["weight"]

            title_lower = title.lower()
            summary_lower = summary.lower()
            keyword_match = any(kw in title_lower or kw in summary_lower for kw in KEYWORDS)

            if weight >= MIN_WEIGHT or keyword_match:
                batch.append(format_article(row))
                batch_ids.append(aid)

                if len(batch) >= BATCH_SIZE:
                    msg = "\n\n".join(batch)
                    success = notify_telegram(msg)
                    alerted_at = datetime.now(timezone.utc).isoformat()
                    if success:
                        for article_id in batch_ids:
                            cursor.execute(
                                "INSERT INTO alerted_articles(article_id, alerted_at) VALUES (?, ?)",
                                (article_id, alerted_at)
                            )
                        print(f"[{alerted_at}] Alerted {len(batch)} article(s).")
                    else:
                        print(f"[{alerted_at}] Failed to alert batch.")
                    conn.commit()
                    batch = []
                    batch_ids = []
            else:
                # Doesn't qualify for alerting, but mark as processed
                alerted_at = datetime.now(timezone.utc).isoformat()
                cursor.execute(
                    "INSERT INTO alerted_articles(article_id, alerted_at) VALUES (?, ?)",
                    (aid, alerted_at)
                )

        # Final leftover batch
        if batch:
            msg = "\n\n".join(batch)
            success = notify_telegram(msg)
            alerted_at = datetime.now(timezone.utc).isoformat()
            if success:
                for article_id in batch_ids:
                    cursor.execute(
                        "INSERT INTO alerted_articles(article_id, alerted_at) VALUES (?, ?)",
                        (article_id, alerted_at)
                    )
                print(f"[{alerted_at}] Alerted final batch of {len(batch)} article(s).")
            else:
                print(f"[{alerted_at}] Failed to alert final batch.")
            conn.commit()

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
