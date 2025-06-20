import os
import threading
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters 
from telegram import Update
import handlers
import db
import scheduler
import pytz
import sys


 

load_dotenv()

bot_token = os.getenv('BOT_TOKEN')
TIMEZONE = os.getenv("TIMEZONE", "UTC") 

if not bot_token:
    raise ValueError('BOT_TOKEN is not set')

def main() -> None:
    db.init_db()
    application = Application.builder().token(bot_token).build()
    message_handler = MessageHandler(filters.TEXT & ~ filters.COMMAND,  handlers.handle_any_message)
    logs_handler = CommandHandler('logs', handlers.show_logs)
    application.add_handler(logs_handler)
    application.add_handler(CommandHandler('remind', handlers.set_reminder))
    application.add_handler(message_handler)
    
    print("Bot is polling for updates. Press Ctrl-C to stop.") 

    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=scheduler.start_scheduler_in_thread, args=(scheduler.scheduler,application.bot,))
    scheduler_thread.daemon = True
    scheduler_thread.start()

     

    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        try:
            scheduler.scheduler.shutdown(wait=False)
        except Exception as e:
            print(f"Error shutting down scheduler: {e}")

        print("Bot stopped by user in the terminal.")
        #sys.exit(0)  # Gracefully exit the program


if __name__ == '__main__':
    main()