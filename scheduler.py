#from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
import datetime
import pytz
import db
 
import asyncio
import utils

TIMEZONE = utils.TIMEZONE 
tz = utils.tz

#scheduler = BlockingScheduler(timezone=tz)
scheduler = AsyncIOScheduler(timezone=tz)

'''def setup_scheduler_jobs(application):  
    """
    Sets up initial scheduler jobs (like loading active reminders from DB on startup).
    The scheduler instance itself (scheduler.scheduler) will be started by the
    application's run_polling method after being attached to the application.
    """
    print(f"Scheduler setup complete in timezone: {datetime.datetime.now(tz).strftime('%Z')}")'''

def schedule_reminder(bot,reminder_id, chat_id, content, timestamp: datetime.datetime):
    job_id = f'reminder_{reminder_id}'
    if timestamp.tzinfo is None: 
        timestamp = tz.localize(timestamp)
        print(f"Warning: Naive datetime provided for reminder {reminder_id}. Assuming timezone {TIMEZONE}.")
    else: 
        timestamp = timestamp.astimezone(tz) 
        
    scheduler.add_job(
        send_reminder,          # The function to run
        DateTrigger(run_date=timestamp), # Run once at this specific date/time
        args=[bot, reminder_id, chat_id, content], # Arguments to pass to send_reminder
        id=job_id,              # Unique ID for the job
        replace_existing=True   # Replace if a job with the same ID already exists (shouldn't happen with unique DB IDs)
    )
    print(f"Reminder {reminder_id} scheduled for user ID: {chat_id}")

'''
        This function schedules a one-time reminder job using the AsyncIOScheduler.
        It takes the bot instance, reminder details, and a timestamp.
        It ensures the timestamp is timezone-aware and converts it to the configured timezone if necessary.
        It then adds the asynchronous `send_reminder` function as a job to the scheduler,
        set to trigger at the specified timestamp, passing the bot and reminder details as arguments.
        It assigns a unique ID to the job derived from the reminder ID.
'''    

 
async def send_reminder(bot, reminder_id, chat_id, content):
    try:
        await bot.send_message(chat_id=chat_id, text=f"🔔 **Reminder:** {content}", parse_mode='Markdown')
        print(f"Reminder sent to {chat_id}")
    except Exception as e:
         
        print(f"Error sending reminder {reminder_id} to {chat_id}: {e}")

    db.deactivate_reminder(reminder_id)
'''
        This is an asynchronous function that is executed by the scheduler when a reminder job triggers.
        It runs within the main asyncio event loop managed by the python-telegram-bot Application.
        It attempts to send the reminder message to the specified chat using `await bot.send_message()`.
        It includes a try...except block to catch and handle any errors that might 
        occur during the message sending process (e.g., if the chat no longer exists or the bot is blocked).
        Finally, it calls `db.deactivate_reminder` to mark the reminder as complete in the database, 
        regardless of message delivery success 
'''    