from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
import datetime

from . import db, utils
from . import client as gemini_client
from .handlers import todo as todo_handlers

scheduler = AsyncIOScheduler(timezone=utils.tz)

async def setup_scheduler_jobs(bot):
    """Sets up and reloads all scheduled jobs on bot startup."""
    active_reminders = db.get_active_reminders()
    for reminder in active_reminders:
        time_stamp = utils.normalize_timestamp(datetime.datetime.fromisoformat(reminder['timestamp']))
        now_tz_aware = datetime.datetime.now(utils.tz)
        
        if time_stamp <= now_tz_aware + datetime.timedelta(seconds=5):
            print(f"Missed reminder (bot inactive): {reminder['content']}")
            try:
                await bot.send_message(
                    chat_id=reminder['chat_id'],
                    text=f"⚠️ Missed Reminder: {reminder['content']}\n(Scheduled for {time_stamp.strftime('%Y-%m-%d %H:%M')})",
                )
            except Exception as e:
                print(f"Error sending missed reminder notification: {e}")
            db.deactivate_reminder(reminder['id'])
            continue
        
        schedule_reminder(bot, reminder['id'], reminder['chat_id'], reminder['content'], time_stamp)

    users = db.get_all_users()
    for user in users:
        schedule_daily_summary_job(bot, user['id'], user['telegram_chat_id'], hour=2, minute=0)
        schedule_hourly_checkin_job(bot, user['id'], user['telegram_chat_id'], start_hour=6, end_hour=23)

    print(f"Scheduler setup complete in timezone: {datetime.datetime.now(utils.tz).strftime('%Z')}")

def schedule_reminder(bot, reminder_id, chat_id, content, timestamp: datetime.datetime):
    job_id = f'reminder_{reminder_id}'
    scheduler.add_job(
        send_reminder,
        DateTrigger(run_date=timestamp),
        args=[bot, reminder_id, chat_id, content],
        id=job_id,
        replace_existing=True
    )
    print(f"Reminder {reminder_id} scheduled for user {chat_id}")

async def send_reminder(bot, reminder_id, chat_id, content):
    try:
        await bot.send_message(chat_id=chat_id, text=f"🔔 Reminder: {content}")
        print(f"Reminder {reminder_id} sent to {chat_id}")
    except Exception as e:
        print(f"Error sending reminder {reminder_id} to {chat_id}: {e}")
    finally:
        db.deactivate_reminder(reminder_id)

def schedule_daily_summary_job(bot, user_id, chat_id, hour, minute):
    job_id = f'daily_summary_{user_id}'
    scheduler.add_job(
        send_summary,
        CronTrigger(hour=hour, minute=minute, timezone=utils.tz),
        args=[bot, user_id, chat_id],
        id=job_id,
        replace_existing=True
    )

async def send_summary(bot, user_id, chat_id):
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    logs = db.get_messages_for_day(user_id, yesterday_str)

    if not logs:
        # No need to send a message if there are no logs
        print(f"No logs for {yesterday_str} for user {user_id}, skipping summary.")
        return

    logs_txt = "\n".join([f"- {utils.normalize_timestamp(datetime.datetime.fromisoformat(ts)).strftime('%H:%M')}: {c}" for ts, c in logs])
    summary_prompt = gemini_client.get_summary_prompt(logs_txt, yesterday_str)
    summary = await gemini_client.get_summary(summary_prompt)

    if summary == "No content generated.":
        print(f"Gemini failed to generate a summary for user {user_id}")
        return

    db.add_summary(user_id, summary, yesterday)
    try:
        await bot.send_message(chat_id=chat_id, text=f"📅 *Summary for {yesterday_str}:*\n\n{summary}", parse_mode='Markdown')
    except Exception as e:
        print(f"Error sending summary to {chat_id}: {e}")

def schedule_hourly_checkin_job(bot, user_id, chat_id, start_hour, end_hour):
    job_id = f'hourly_checkin_{user_id}'
    hours = f'{start_hour}-{end_hour}' if end_hour >= start_hour else f'{start_hour}-23,0-{end_hour}'
    scheduler.add_job(
        send_hourly_checkin,
        CronTrigger(hour=hours, minute=0, timezone=utils.tz),
        args=[bot, user_id, chat_id],
        id=job_id,
        replace_existing=True
    )

async def send_hourly_checkin(bot, user_id, chat_id):
    greeting = "Hey there! 👋 Whatcha doing?"
    todo_list_text, todo_list_markup = todo_handlers._get_formatted_todos_content(user_id)

    try:
        await bot.send_message(chat_id=chat_id, text=greeting)
        await bot.send_message(
            chat_id=chat_id,
            text=todo_list_text,
            reply_markup=todo_list_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error sending hourly check-in to {chat_id}: {e}")