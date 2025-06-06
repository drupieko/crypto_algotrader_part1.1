#!/usr/bin/env python3
"""
news_acquisition.py

Loop every 120 seconds, fetch a fixed set of RSS feeds,
dedupe by URL, count how many sources provided the same URL (weight),
and insert new articles into SQLite (fetched_articles + raw_news_queue).
"""

import os
from datetime import datetime, timezone
import time
import hashlib
import sqlite3
import feedparser
from textwrap import shorten

# === LOGGING SETUP ===
log_file = "/home/tito/crypto_algotrader_part1/logs/part1/news_acquisition.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)

def log(message):
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

log("Script execution started")

# === DB PATH ===
DB_PATH = "/home/tito/crypto_algotrader_part1/part1/db/crypto.db"

# === RSS FEEDS ===
RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://bitcoinmagazine.com/.rss/full/",
    "https://cryptopotato.com/feed/",
    "https://cryptobriefing.com/feed/",
    "https://crypto.news/feed/",
    "https://coinjournal.net/feed/",
    "https://rss.feedspot.com/cryptonewsz.xml"
]

FETCH_INTERVAL = 120  # seconds

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def compute_article_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()

def fetch_all_feeds():
    """
    Parse each RSS feed, return a dict mapping URL -> dict(title, summary, published, weight).
    """
    url_map = {}  # url -> {title, summary, published, weight}
    for feed_url in RSS_FEEDS:
        d = feedparser.parse(feed_url)
        log(f"Fetched feed: {feed_url} with {len(d.entries)} entries.")
        for entry in d.entries:
            link = entry.get("link")
            if not link:
                continue
            title = entry.get("title", "").strip()
            summary = entry.get("summary", "") or entry.get("description", "")
            published = entry.get("published") or entry.get("updated") or ""
            if link not in url_map:
                url_map[link] = {
                    "title": title,
                    "summary": summary,
                    "published": published,
                    "weight": 1
                }
            else:
                url_map[link]["weight"] += 1
    return url_map

def main_loop():
    while True:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            now_ts = datetime.now(timezone.utc).isoformat()
            url_map = fetch_all_feeds()
            log(f"Fetched {len(url_map)} unique URLs from {len(RSS_FEEDS)} feeds.")

            new_articles = 0

            for link, info in url_map.items():
                article_id = compute_article_id(link)

                # Skip if already seen
                cursor.execute(
                    "SELECT 1 FROM fetched_articles WHERE article_id = ?",
                    (article_id,)
                )
                if cursor.fetchone():
                    continue

                weight = info["weight"]

                # Insert into fetched_articles
                cursor.execute(
                    "INSERT INTO fetched_articles (article_id, fetched_at, weight) VALUES (?, ?, ?)",
                    (article_id, now_ts, weight)
                )

                # Insert into raw_news_queue
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO raw_news_queue
                      (article_id, title, summary, link, published_at, weight)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        article_id,
                        info["title"],
                        info["summary"],
                        link,
                        info["published"],
                        weight
                    )
                )

                log(f"New article queued: {shorten(info['title'], width=60)} (weight={weight})")
                new_articles += 1

            conn.commit()
            conn.close()
            log(f"Cycle complete: {new_articles} new articles added.")
        except Exception as e:
            error_ts = datetime.now(timezone.utc).isoformat()
            log(f"ERROR: {e}")
        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main_loop()
