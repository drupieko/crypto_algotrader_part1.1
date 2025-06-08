import asyncio
import json
import sqlite3
import websockets
import yaml
from datetime import datetime

BINANCE_WS = "wss://stream.binance.com:9443/ws"

DB_PATH = "/home/tito/crypto_algotrader_part1/part1/db/crypto.db"
CONFIG_PATH = "/home/tito/crypto_algotrader_part1/part2/config/binance_keys.yaml"

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_data_1m (
            symbol TEXT,
            timestamp INTEGER,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY(symbol, timestamp)
        )
    """)
    conn.commit()
    conn.close()

async def handle_stream(symbols):
    stream_name = '/'.join([f"{s.lower()}@kline_1m" for s in symbols])
    url = f"{BINANCE_WS}/{stream_name}"

    async with websockets.connect(url) as websocket:
        while True:
            try:
                msg = await websocket.recv()
                data = json.loads(msg)
                k = data['k']
                save_candle(
                    symbol=k['s'],
                    timestamp=k['t'],
                    o=k['o'], h=k['h'], l=k['l'], c=k['c'], v=k['v']
                )
            except Exception as e:
                print(f"[{datetime.utcnow()}] Error: {e}")

def save_candle(symbol, timestamp, o, h, l, c, v):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO market_data_1m 
            (symbol, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (symbol, timestamp, o, h, l, c, v))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[{datetime.utcnow()}] DB Error: {e}")

def get_symbols():
    from binance.client import Client

    cfg = load_config()
    client = Client(cfg['binance']['api_key'], cfg['binance']['api_secret'])
    all_symbols = [
        s['symbol'] for s in client.futures_exchange_info()['symbols']
        if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT'
    ]
    return [s for s in all_symbols if s not in cfg['binance']['symbols_excluded']]

if __name__ == "__main__":
    init_db()
    symbols = get_symbols()
    print(f"Tracking {len(symbols)} symbols...")
    asyncio.run(handle_stream(symbols))
