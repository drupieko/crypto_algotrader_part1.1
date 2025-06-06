#!/usr/bin/env python3
import time
import sqlite3
import os
import feedparser

# Path to the SQLite database created earlier
DB_PATH = os.path.expanduser("~/crypto_algotrader_part1/crypto_part1.db")

# List of RSS feed URLs for crypto news (you can add or remove URLs here)
RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://cryptonews.com/news/feed.rss",
    "https://news.bitcoin.com/feed/"
]

# Interval (in seconds) between fetches
FETCH_INTERVAL = 120  # 2 minutes

def get_db_connection():
    """Open a connection to the SQLite database (with row access)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def article_already_seen(conn, article_id):
    """Check if article_id exists in fetched_articles table."""
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM fetched_articles WHERE article_id = ?", (article_id,))
    return cur.fetchone() is not None

def mark_article_seen(conn, article_id, fetched_at):
    """Insert a new article_id into fetched_articles to mark it seen."""
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO fetched_articles (article_id, fetched_at) VALUES (?, ?)",
        (article_id, fetched_at)
    )
    conn.commit()

def enqueue_raw_article(conn, article_id, headline, url, summary, published_at):
    """Insert a new row into raw_news_queue."""
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO raw_news_queue (article_id, headline, url, summary, published_at)
            VALUES (?, ?, ?, ?, ?)
        """, (article_id, headline, url, summary, published_at))
        conn.commit()
    except sqlite3.IntegrityError:
        # If the same article_id already exists in raw_news_queue, ignore
        pass

def fetch_and_store():
    """Fetch each RSS feed, dedupe, and store new articles."""
    conn = get_db_connection()
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            # If feedparser encountered a problem parsing this feed, skip it
            print(f"[Warning] Could not parse RSS feed: {feed_url}")
            continue

        for entry in feed.entries:
            # Use a unique article_id: prefer entry.id if available, else entry.link
            article_id = entry.get("id", entry.get("link", None))
            if not article_id:
                # If neither ID nor link exists, skip this item
                continue

            # If we’ve already seen this article, skip
            if article_already_seen(conn, article_id):
                continue

            # Extract fields (some entries may not have summary; handle gracefully)
            headline = entry.get("title", "").strip()
            url = entry.get("link", "").strip()
            summary = entry.get("summary", "").strip() if entry.get("summary") else ""
            published_at = entry.get("published", entry.get("updated", ""))

            # Mark as seen and insert into raw_news_queue
            fetched_at = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            mark_article_seen(conn, article_id, fetched_at)
            enqueue_raw_article(conn, article_id, headline, url, summary, published_at)
            print(f"[New] {headline}")

    conn.close()

def main():
    print("=== Starting news_acquisition.py ===")
    while True:
        try:
            fetch_and_store()
        except Exception as e:
            print(f"[Error] Exception during fetch_and_store: {e}")
        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main()
