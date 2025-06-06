#!/usr/bin/env python3
import sqlite3
import os
import sys

# Path for the SQLite database file
DB_PATH = os.path.expanduser("~/crypto_algotrader_part1/crypto_part1.db")

def create_tables(conn):
    cur = conn.cursor()
    # 1. Table for deduplication of fetched articles
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fetched_articles (
        article_id   TEXT PRIMARY KEY,
        fetched_at   DATETIME NOT NULL
    );
    """)

    # 2. Raw news queue (articles just fetched)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_news_queue (
        article_id   TEXT PRIMARY KEY,
        headline     TEXT NOT NULL,
        url          TEXT NOT NULL,
        summary      TEXT,
        published_at DATETIME NOT NULL
    );
    """)

    # 3. Scored news queue (sentiment scoring results)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scored_news_queue (
        article_id      TEXT PRIMARY KEY,
        timestamp       DATETIME NOT NULL,
        headline        TEXT NOT NULL,
        url             TEXT NOT NULL,
        sentiment_label TEXT NOT NULL,
        intensity       REAL NOT NULL,
        relevance_score REAL NOT NULL
    );
    """)

    # 4. Tradable news queue (filtered “tradable” items)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tradable_news_queue (
        article_id      TEXT PRIMARY KEY,
        timestamp       DATETIME NOT NULL,
        headline        TEXT NOT NULL,
        url             TEXT NOT NULL,
        sentiment_label TEXT NOT NULL,
        intensity       REAL NOT NULL,
        relevance_score REAL NOT NULL,
        processed       INTEGER NOT NULL DEFAULT 0
    );
    """)

    conn.commit()

def main():
    # Ensure directory exists
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.isdir(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory '{db_dir}':", e)
            sys.exit(1)

    # Create (or open) the database
    try:
        conn = sqlite3.connect(DB_PATH)
    except Exception as e:
        print("Failed to connect to SQLite database:", e)
        sys.exit(1)

    # Create tables
    try:
        create_tables(conn)
        print(f"Database initialized at:\n    {DB_PATH}\nAll tables created successfully.")
    except Exception as e:
        print("Error creating tables:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
