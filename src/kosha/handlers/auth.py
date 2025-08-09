
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from ..core.config import MY_CHAT_ID

def restricted_access(func):
    """Decorator to restrict access to only the allowed chat ID."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_chat:
            return

        chat_id = update.effective_chat.id
        
        if MY_CHAT_ID and str(chat_id) != MY_CHAT_ID:
            print(f"Unauthorized access denied for chat ID: {chat_id}")
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapped
