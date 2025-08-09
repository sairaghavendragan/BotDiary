import datetime
import pytz
from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from .auth import restricted_access
from .. import db, utils

@restricted_access
async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles any non-command message by logging it to the journal."""
    if not update.message or not update.message.text:
        return
        
    chat_id = update.message.chat_id
    content = update.message.text
    print(f"Logging message for chat_id: {chat_id}")

    user_id = db.get_or_create_user(chat_id)
    db.log_message(user_id, content)

    await update.message.reply_text('Saved to your journal!')

@restricted_access
async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the journal logs for the current day."""
    if not update.message:
        return

    chat_id = update.message.chat_id
    user_id = db.get_or_create_user(chat_id)
    today = datetime.date.today()
    today_str = today.strftime('%Y-%m-%d')
    
    logs = db.get_messages_for_day(user_id, today_str)
    
    if not logs:
        response_text = f"No logs found for today ({today_str})."
    else:
        response_text = f"Logs for today ({today_str}):\n"
        for timestamp, content in logs:
            try:
                ts_obj = utils.normalize_timestamp(datetime.datetime.fromisoformat(timestamp))
                time_str = ts_obj.strftime('%H:%M')
            except ValueError:
                time_str = timestamp  # Fallback
            response_text += f"- {time_str}: {content}\n"

    escaped_response = escape_markdown(response_text, version=2)
    await update.message.reply_text(escaped_response, parse_mode='MarkdownV2')

@restricted_access
async def get_specific_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Retrieves a summary for a specific date."""
    if not update.message or not context.args:
        await update.message.reply_text("Usage: /summary [date] (e.g., /summary yesterday)")
        return

    chat_id = update.message.chat_id
    user_id = db.get_or_create_user(chat_id)
    input_txt = " ".join(context.args)
    date = utils.parse_datetime(input_txt)

    if date is None:
        await update.message.reply_text("Invalid date format. Please try something like 'yesterday' or '2023-10-27'.")
        return

    summary = db.get_summary_for_user(user_id, date.date())
    
    if not summary:
        await update.message.reply_text(f"No summary found for {date.strftime('%Y-%m-%d')}.")
        return

    await update.message.reply_text(summary['content'], parse_mode='Markdown')
