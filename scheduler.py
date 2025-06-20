from apscheduler.schedulers.blocking import BlockingScheduler
#from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
import datetime
import pytz
import db
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

TIMEZONE = os.getenv('TIMEZONE')    
try:
    tz = pytz.timezone(TIMEZONE)
except pytz.exceptions.UnknownTimeZoneError:
    raise ValueError(f"Invalid TIMEZONE: {TIMEZONE}")

scheduler = BlockingScheduler(timezone=tz)
#scheduler = AsyncIOScheduler(timezone=tz)

def start_scheduler_in_thread(scheduler_instance,bot):
    try:

        scheduler_instance.start()
    except  (KeyboardInterrupt, SystemExit):
        print(f"scheduler stopped by user in the terminal.")
        scheduler_instance.shutdown()
        print("scheduler stopped.")

def schedule_reminder(bot,reminder_id, chat_id, content, timestamp):
    job_id = f'reminder_{reminder_id}'
    if timestamp.tzinfo is None:
        # If the datetime is naive, assume it's in the configured TIMEZONE
        timestamp = tz.localize(timestamp)
        print(f"Warning: Naive datetime provided for reminder {reminder_id}. Assuming timezone {TIMEZONE}.")
    else:
        # Convert to the configured TIMEZONE if it's a different timezone
        timestamp = timestamp.astimezone(tz)

        
    scheduler.add_job(
        send_reminder_sync_wrapper,          # The function to run
        DateTrigger(run_date=timestamp), # Run once at this specific date/time
        args=[bot, reminder_id, chat_id, content], # Arguments to pass to send_reminder
        id=job_id,              # Unique ID for the job
        replace_existing=True   # Replace if a job with the same ID already exists (shouldn't happen with unique DB IDs)
    )
    print(f"Reminder {reminder_id} scheduled for user ID: {chat_id}")

def send_reminder_sync_wrapper(bot, reminder_id, chat_id, content):
    try:
        asyncio.run(send_reminder(bot, reminder_id, chat_id, content))
    except Exception as e:
        # Log any errors during sending (e.g., user blocked bot)
        print(f"Error sending reminder {reminder_id} to {chat_id}: {e}")

    db.deactivate_reminder(reminder_id)

async def send_reminder(bot, reminder_id, chat_id, content):
    try:
        await bot.send_message(chat_id=chat_id, text=f"🔔 **Reminder:** {content}", parse_mode='Markdown')
        print(f"Reminder sent to {chat_id}")
    except Exception as e:
        # Log any errors during sending (e.g., user blocked bot)
        print(f"Error sending reminder {reminder_id} to {chat_id}: {e}")

    #db.deactivate_reminder(reminder_id)