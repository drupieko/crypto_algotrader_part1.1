from dotenv import load_dotenv
import os

load_dotenv()  # reads .env file in current directory

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

if not API_ID or not API_HASH:
    raise ValueError("API_ID or API_HASH not set in .env file")
