
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TIMEZONE = os.getenv('TIMEZONE', 'UTC')
MY_CHAT_ID = os.getenv('MY_CHAT_ID')

if not BOT_TOKEN:
    raise ValueError('BOT_TOKEN is not set in the .env file')

if not GEMINI_API_KEY:
    raise ValueError('GEMINI_API_KEY is not set in the .env file')
