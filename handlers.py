from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
import db
import datetime
from dateutil.parser import parse
from dateparser.search import search_dates
import scheduler
import pytz 
import utils

 
TIMEZONE = utils.TIMEZONE 
tz = utils.tz
async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id 
    content = update.message.text
    print(update.message.text)

    user_id = db.get_or_create_user(chat_id)
    db.log_message(user_id, content)

    await update.message.reply_text('Saved to your journal!')

'''
    This asynchronous function handles any incoming text message that is not recognized as a command.
    It retrieves the chat ID and message content from the update.
    It interacts with the database to get or create the user associated with the chat and logs the message content.
    Finally, it sends a confirmation message back to the user using `await update.message.reply_text()`.
    The database interactions (`db.get_or_create_user`, `db.log_message`) are synchronous blocking calls 
    but are quick enough not to significantly block the event loop in typical scenarios.
'''    

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

'''
    This asynchronous function handles the `/logs` command.
    It retrieves the user's chat ID, gets the user in the database, and fetches log messages for the current day.
    It then formats the retrieved log messages into a human-readable string, a
    ttempting to parse and localize timestamps to the configured timezone.
    It handles cases where no logs are found.
    Finally, it escapes the resulting text for MarkdownV2 compatibility and
      sends it back to the user using `await update.message.reply_text()` with `parse_mode='MarkdownV2'`.
    It includes error handling for parsing timestamp strings from the database.
'''


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
    
     
    reminder_message = ""
    parsed_datetime = None 


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

     
    parsed_datetime = utils.normalize_timestamp(parsed_datetime)
    # Ensure the reminder is in the future (give a small grace period, e.g., 5 seconds)
    now_tz_aware = datetime.datetime.now(tz)
    if parsed_datetime <= now_tz_aware + datetime.timedelta(seconds=5):
        print(f"Reminder time too soon: {parsed_datetime}, now: {now_tz_aware}")
        await update.message.reply_text("That time seems to be in the past or too soon. Please set a reminder for the future.")
        return
    
    reminder_id = db.set_reminder(user_id, reminder_message, parsed_datetime)
    scheduler.schedule_reminder(context.bot,reminder_id, chat_id, reminder_message, parsed_datetime)
    await update.message.reply_text(f"Reminder {reminder_message} set for {parsed_datetime.strftime('%Y-%m-%d %H:%M')}.")
'''
   -- This asynchronous function handles the `/remind` command.
   -- It retrieves the user's chat ID and command arguments.
   -- It validates if arguments are provided and calls `utils.reminder_input` 
      to parse the input string into a datetime and the reminder message.
   -- It performs error handling if parsing fails or no message content is found, providing usage instructions.
   -- It ensures the parsed datetime is timezone-aware and converts it to the configured timezone (`tz`).
   -- It checks if the reminder time is in the future, providing an error if it's in the past or too soon.
   -- If the input is valid, it saves the reminder to the database using `db.set_reminder` to get a unique ID.
   -- It then schedules the reminder job using `scheduler.schedule_reminder`,
     passing the bot instance (`context.bot`) and the reminder details.
   -- Finally, it sends a confirmation message back to the user using `await update.message.reply_text()`.
     
'''    

async def get_specific_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id  = update.message.chat_id
    user_id = db.get_or_create_user(chat_id)
    command_args = context.args
    if not command_args:
        await update.message.reply_text("Usage: `/summary [date]`\n\n"
            "Examples:\n"
            "`/summary 2025-10-27`\n" 
            "`/summary yesterday`\n " 
            "`/summary 23 july 2025`", 
            parse_mode='Markdown' )    
        return
    input_txt = " ".join(command_args)
    date = utils.parse_datetime(input_txt)
    if date is None:
        await update.message.reply_text("Invalid date format. Please use one of the following formats:\n"
            "`/summary 2025-10-27`\n" 
            "`/summary yesterday`\n " 
            "`/summary 23 july 2025`" ,
            parse_mode='Markdown' )    
        return
    summary = db.get_summary_for_user(user_id, date.date())
    if summary is None:
        await update.message.reply_text(f"No summary found for the specified date.{date.strftime('%Y-%m-%d')}")
        return 
    await update.message.reply_text(summary['content'],parse_mode='Markdown')