
import datetime
from telegram import Update
from telegram.ext import ContextTypes

from .auth import restricted_access
from .. import db, utils, scheduler

@restricted_access
async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets a reminder for the user."""
    if not update.message or not context.args:
        await update.message.reply_text("Usage: /remind [time/date] [message]")
        return

    chat_id = update.message.chat_id
    user_id = db.get_or_create_user(chat_id)
    
    full_input_text = " ".join(context.args)
    parsed_datetime, reminder_message = utils.reminder_input(full_input_text)

    if not parsed_datetime or not reminder_message:
        await update.message.reply_text("Could not parse the reminder. Please use a clear time and message.")
        return

    # Ensure the reminder is in the future
    now_tz_aware = datetime.datetime.now(utils.tz)
    if parsed_datetime <= now_tz_aware + datetime.timedelta(seconds=5):
        await update.message.reply_text("That time seems to be in the past. Please set a reminder for the future.")
        return
    
    reminder_id = db.set_reminder(user_id, reminder_message, parsed_datetime)
    if context.bot:
        scheduler.schedule_reminder(context.bot, reminder_id, chat_id, reminder_message, parsed_datetime)
    
    await update.message.reply_text(f"Reminder set for {parsed_datetime.strftime('%Y-%m-%d %H:%M')}: {reminder_message}")
