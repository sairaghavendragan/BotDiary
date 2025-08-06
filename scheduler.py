#from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
import datetime
 
import db
import gemini_client
import handlers
 
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

async def setup_scheduler_jobs(bot):  
    """
    Sets up initial scheduler jobs (like loading active reminders from DB on startup).
    The scheduler instance itself (scheduler.scheduler) will be started by the
    application's run_polling method after being attached to the application.
    """
     
    active_reminders = db.get_active_reminders()
    for reminder in active_reminders:
        time_stamp = datetime.datetime.fromisoformat(reminder['timestamp'])
        time_stamp = utils.normalize_timestamp(time_stamp)
        now_tz_aware = datetime.datetime.now(tz)
        if time_stamp <= now_tz_aware + datetime.timedelta(seconds=5):
            print(f"Reminder couldnt reach you because bot was inactive.remindercontent: {reminder['content']}")
            await bot.send_message(
                                        chat_id=reminder['chat_id'],
                                        text=f"⚠️ Missed Reminder: {reminder['content']}\n(Bot was inactive at the scheduled time: {time_stamp.strftime('%Y-%m-%d %H:%M:%S %Z')})",
                                        parse_mode='Markdown'
                                    )
            db.deactivate_reminder(reminder['id'])
            continue
        schedule_reminder(bot,reminder['id'], reminder['chat_id'], reminder['content'], time_stamp)
    users = db.get_all_users()
    for user in users:
        schedule_daily_summary_job(bot, user['id'], user['telegram_chat_id'],hour=2, minute=0)   
        schedule_hourly_checkin_job(bot, user['id'], user['telegram_chat_id'],start_hour=6, end_hour=23)

    print(f"Scheduler setup complete in timezone: {datetime.datetime.now(tz).strftime('%Z')}")


def schedule_reminder(bot,reminder_id, chat_id, content, timestamp: datetime.datetime):
    job_id = f'reminder_{reminder_id}'
    
     
        
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

def schedule_daily_summary_job(bot, user_id, chat_id, hour, minute):
    job_id = f'daily_summary_{user_id}'
    scheduler.add_job(
        send_summary,          # The function to run
        CronTrigger(hour=hour, minute=minute,timezone=tz), # Run once at midnight
        args=[bot, user_id, chat_id], # Arguments to pass to send_summary
        id=job_id,              # Unique ID for the job
        replace_existing=True   # Replace if a job with the same ID already exists (shouldn't happen with unique DB IDs)
    )
    print(f"Summary scheduled for user ID: {user_id}")

async def send_summary(bot, user_id, chat_id):
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d') 
    #today = datetime.date.today()
    #today_str = today.strftime('%Y-%m-%d')
    logs = db.get_messages_for_day(user_id, yesterday_str)
    #test_logs = db.get_messages_for_day(user_id, today_str)
    #logs = test_logs 
     

    if not logs :
        
        await bot.send_message(chat_id=chat_id, text=f"📅 No logs found for today: {yesterday_str} . No summary generated" )
    logs_txt = ""
    for timestamp, content in logs:
        try:
            ts_obj = datetime.datetime.fromisoformat(timestamp)
            if ts_obj.tzinfo is None:
                ts_obj = utils.tz.localize(ts_obj)  # Localize to UTC if naive datetime
            else:
                ts_obj = ts_obj.astimezone(tz)
            time_str = ts_obj.strftime('%H:%M')
        except ValueError:
            time_str = timestamp

        logs_txt += f"- {time_str}: {content}\n"    
    summary_prompt = gemini_client.get_summary_prompt(logs_txt, yesterday_str)
    summary = await gemini_client.get_summary(summary_prompt)
    if summary == "No content generated.":
        await bot.send_message(chat_id=chat_id, text=f"Gemini couldnt generate a summary . No summary generated" )
        return
    db.add_summary(user_id, summary, yesterday)

    try:
        await bot.send_message(chat_id=chat_id, text=f"📅 **Summary for {yesterday_str}:**\n\n{summary}", parse_mode='Markdown')
    except Exception as e:
        print(f"Error sending summary to {chat_id}: {e}")
         

def schedule_hourly_checkin_job(bot, user_id, chat_id, start_hour, end_hour ):
    job_id = f'hourly_checkin_{user_id}'
    if end_hour >= start_hour:
        hours = f'{start_hour}-{end_hour}'
    else:
        # e.g., start_hour=6, end_hour=2 -> '6-23,0-2'
        hours = f'{start_hour}-23,0-{end_hour}'         
    scheduler.add_job(
        send_hourly_checkin,          # The function to run
        CronTrigger(hour=hours,minute=0, timezone=tz), # Run once at midnight
        args=[bot, user_id, chat_id], # Arguments to pass to send_summary
        id=job_id,              # Unique ID for the job
        replace_existing=True   # Replace if a job with the same ID already exists (shouldn't happen with unique DB IDs)
    )
    print(f"Hourly checkin scheduled for user ID: {user_id}")

async def send_hourly_checkin(bot, user_id, chat_id):
    greeting = "Hey there! 👋 Whatcha doing?"
    
     
    todo_list_text, todo_list_markup = handlers._get_formatted_todos_content(user_id)

     

    
    try:
        await bot.send_message(chat_id=chat_id, text=greeting, parse_mode='Markdown')
        await bot.send_message(
            chat_id=chat_id,
            text=todo_list_text,
            reply_markup=todo_list_markup, # Include the inline keyboard if there are todos
            parse_mode='Markdown'
        )
        print(f"Hourly check-in sent to {chat_id}")
    except Exception as e:
        print(f"Error sending hourly check-in to {chat_id}: {e}")
    