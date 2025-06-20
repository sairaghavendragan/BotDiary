from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
import db
import datetime
from dateutil.parser import parse
from dateparser.search import search_dates
import scheduler
import pytz
import os
from dotenv import load_dotenv
import utils

load_dotenv()
TIMEZONE = os.getenv('TIMEZONE')    
try:
    tz = pytz.timezone(TIMEZONE)
except pytz.exceptions.UnknownTimeZoneError:
    raise ValueError(f"Invalid TIMEZONE: {TIMEZONE}")

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id 
    content = update.message.text
    print(update.message.text)

    user_id = db.get_or_create_user(chat_id)
    db.log_message(user_id, content)

    await update.message.reply_text('Saved to your journal!')

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    user_id = db.get_or_create_user(chat_id)
    today = datetime.date.today()
    today_str = today.strftime('%Y-%m-%d')
    #yesterday = today - datetime.timedelta(days=1)
    #yesterday_str = yesterday.strftime('%Y-%m-%d')
    logs = db.get_messages_for_day(user_id, today_str)
    response_text = ""
    if logs:
        response_text += f"Logs for today ({today_str}):\n"
        for timestamp, content in logs:
            try:
                ts_obj = datetime.datetime.fromisoformat(timestamp)
                if ts_obj.tzinfo is None:
                    ts_obj = pytz.utc.localize(ts_obj)  # Localize to UTC if naive datetime
                
                # Convert the timestamp to the user's timezone
                ts_obj = ts_obj.astimezone(tz)
                time_str = ts_obj.strftime('%H:%M')
                 
             
            except ValueError:
                 # Handle potential formatting issues
                 time_str = timestamp
             
            response_text += f"- {time_str}: {content}\n" 
               
        response_text += "\n" # Add a newline for separation
    else:
        response_text += f"No logs found for today ({today_str})."
        #response_text= escape_markdown(response_text,version=2)

    escaped_response = escape_markdown(response_text,version=2)
    await update.message.reply_text(escaped_response,parse_mode='MarkdownV2')  

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    user_id = db.get_or_create_user(chat_id)
    command_args = context.args

    if not command_args:
        await update.message.reply_text("Usage: `/remind [time/date] [message]`\n\n"
            "Examples:\n"
            "`/remind in 1 hour Call Mom`\n"
            "`/remind tomorrow 10am Buy milk`\n"
            "`/remind 2023-10-27 14:30 Project deadline`\n"
            "`/remind next monday morning Team meeting`",
            parse_mode='Markdown' )    
        return
    
    time_string = ""
    reminder_message = ""
    parsed_datetime = None
    message_start_index = 0


    full_input_text = " ".join(command_args) 
    parsed_datetime,reminder_message = utils.reminder_input(full_input_text)
     

    if parsed_datetime is None or not reminder_message:
        await update.message.reply_text("Invalid time format. Please use one of the following formats:\n"
            "`/remind in 1 hour Call Mom`\n"
            "`/remind tomorrow 10am Buy milk`\n"
            "`/remind 2023-10-27 14:30 Project deadline`\n"
            "`/remind next monday morning Team meeting`",
            parse_mode='Markdown' )    
        return

     
    if parsed_datetime.tzinfo is None:
        # Assume naive datetime is in the configured TIMEZONE
        parsed_datetime = tz.localize(parsed_datetime)
    else:
        # If timezone-aware, convert it to our configured TIMEZONE
        parsed_datetime = parsed_datetime.astimezone(tz)

    # Ensure the reminder is in the future (give a small grace period, e.g., 5 seconds)
    now_tz_aware = datetime.datetime.now(tz)
    if parsed_datetime <= now_tz_aware + datetime.timedelta(seconds=5):
        print(f"Reminder time too soon: {parsed_datetime}, now: {now_tz_aware}")
        await update.message.reply_text("That time seems to be in the past or too soon. Please set a reminder for the future.")
        return
    
    reminder_id = db.set_reminder(user_id, reminder_message, parsed_datetime)
    scheduler.schedule_reminder(context.bot,reminder_id, chat_id, reminder_message, parsed_datetime)
    await update.message.reply_text(f"Reminder {reminder_message} set for {parsed_datetime.strftime('%Y-%m-%d %H:%M')}.")