import asyncio
import feedparser
import httpx
import os
from pyrogram import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID  = os.getenv("CHAT_ID")
AGENT_B_ENDPOINT = os.getenv("AGENT_B_URL", "http://127.0.0.1:8000/ingest")

if not API_ID or not API_HASH or not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("Missing API_ID, API_HASH, BOT_TOKEN or CHAT_ID in .env")

# Pass full auth to Client
app = Client("sentiment_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

RSS_FEEDS = [
    "https://www.forexlive.com/feed/news/",
    "https://www.fxstreet.com/rss/news"
]

async def main():
    await app.start()
    print("Agent A (bot) started")

    seen = set()
    while True:
        for url in RSS_FEEDS:
            feed = feedparser.parse(url)
            if feed.bozo:
                print(f"[Warning] Could not parse RSS feed: {url}")
                continue

            for entry in feed.entries[:10]:
                uid = entry.get("id") or entry.get("link")
                if uid in seen:
                    continue
                seen.add(uid)

                headline = entry.get("title", "No Title").strip()
                link     = entry.get("link", "").strip()
                message  = f"📰 {headline}\n{link}"

                try:
                    await app.send_message(chat_id=CHAT_ID, text=message)
                    print(f"[Telegram] Sent: {headline[:30]}…")
                except Exception as e:
                    print(f"[Error] Telegram send failed: {e}")

                async with httpx.AsyncClient() as client:
                    try:
                        resp = await client.post(
                            AGENT_B_ENDPOINT,
                            json={"headline": headline, "link": link},
                            timeout=10.0
                        )
                        if resp.status_code != 200:
                            print(f"[Warning] Agent B responded {resp.status_code}")
                    except Exception as e:
                        print(f"[Error] Agent B POST failed: {e}")

                await asyncio.sleep(1)

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
