# main.py

import os
from dotenv import load_dotenv

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler  
)
from telegram import Update  
import handlers  
import db  
import scheduler  
import pytz  
import sys  
import asyncio  

'''
        imported os and dotenv module's load_dotenv  to load environment variables from .env file
        imported needed modules from telegram.ext,telegram
        imported handlers,db,scheduler which are the other python files we wrote
        imported pytz and sys and asyncio modules
 '''

load_dotenv()

bot_token = os.getenv('BOT_TOKEN')
TIMEZONE = os.getenv("TIMEZONE", "UTC")

if not bot_token:
    raise ValueError('BOT_TOKEN is not set')


async def post_init_callback(application: Application) -> None:
     
    print("Running post_init_callback...")
    try:
        # Start the AsyncIOScheduler within the bot's event loop
        scheduler.scheduler.start()
        print("Scheduler started and integrated with asyncio loop.")
        await scheduler.setup_scheduler_jobs(application.bot)
        print("Post-initialization complete.")

    except Exception as e:
        print(f"Error during post_init_callback: {e}")
        # If scheduler fails to start, it's a critical error for reminder functionality
        # sys.exit(1)  
'''
        This function is called asynchronously by python-telegram-bot after the
        Application object is fully initialized but BEFORE it starts polling for updates.
        It runs within the application's main asyncio event loop.

        This is CRITICAL for starting the AsyncIOScheduler correctly because
        AsyncIOScheduler needs an asyncio event loop to be running when .start() is called.

        By using the post_init_callback hook, we ensure scheduler.start() is called
        in the correct asynchronous context, integrated with the bot's event loop.
        The try...except block is used to handle potential errors during scheduler startup.


'''

 
def main() -> None:
    
    db.init_db()
    print("Database initialized.") 
    application = Application.builder().token(bot_token).post_init(post_init_callback).build() 
    message_handler = MessageHandler(filters.TEXT & ~ filters.COMMAND, handlers.handle_any_message) 
    logs_handler = CommandHandler('logs', handlers.show_logs)
    set_reminder_handler = CommandHandler('remind', handlers.set_reminder) 
    add_todo_handler = CommandHandler('todo', handlers.add_new_todo) 
    show_todos_handler = CommandHandler('todos', handlers.show_daily_todos) 
    summary_handler = CommandHandler('summary', handlers.get_specific_summary)
    

    gemini_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("gemini", handlers.start_gemini)],
        states={
            handlers.GEMINI_CONVERSATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.continue_gemini_chat),
            ]
        },
        fallbacks=[
            CommandHandler("endgemini", handlers.end_gemini_conversation),
            CommandHandler("logs", handlers.end_gemini_conversation), # End chat if other commands are used
            CommandHandler("remind", handlers.end_gemini_conversation),
            CommandHandler("todo", handlers.end_gemini_conversation),
            CommandHandler("todos", handlers.end_gemini_conversation),
            CommandHandler("summary", handlers.end_gemini_conversation),
            # Add any other top-level commands here that should exit Gemini chat
        ],
        allow_reentry=True # Allows starting new conversations even if already in one
    )

    application.add_handler(gemini_conversation_handler)






    application.add_handler(logs_handler) 
    application.add_handler(set_reminder_handler)
    application.add_handler(summary_handler)
    application.add_handler(add_todo_handler)
    application.add_handler(show_todos_handler)
    application.add_handler(CallbackQueryHandler(handlers.handle_todo_callback))
     
    application.add_handler(message_handler) 

    print("Bot application built. Starting polling...")

     
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt: 
        print("\nKeyboard interrupt received. Stopping bot and scheduler.")
        try: 
             scheduler.scheduler.shutdown(wait=False)
             print("Scheduler stopped.")
        except Exception as e:
            print(f"Error shutting down scheduler: {e}")

        print("Bot stopped by user in the terminal.") 
    except Exception as e:
        print(f"An unexpected error occurred during polling: {e}")
         
        try:
            scheduler.scheduler.shutdown(wait=False)
            print("Scheduler stopped due to polling error.")
        except Exception as se:
            print(f"Error shutting down scheduler after polling error: {se}")
        sys.exit(1)

'''
            Main synchronous function to set up and run the bot application.
    This function serves as the entry point when the script is executed directly.
    It performs the initial synchronous setup steps and then starts the bot's
    polling loop, which internally manages the asyncio event loop and handles updates.

    Key steps:
    - Initializes the database (synchronous).
    - Builds the Application instance using Application.builder(), passing the bot token.
    - Registers the `post_init_callback` using `.post_init()` to handle asynchronous setup 
      (like starting the scheduler) within the event loop *after* the application is built.
    - Adds various Handler instances to the application to route specific types of updates
       (commands, messages) to corresponding asynchronous functions in `handlers.py`.
    - Starts the bot's main event loop and begins fetching updates from 
     Telegram using `application.run_polling()`. This call is blocking and will run indefinitely until interrupted.
     And crucially before fetching updates it will look for the async functions scheduled such as
     `post_init_callback` and runs them.
    - Includes error handling using try...except blocks to catch `KeyboardInterrupt` 
      (for graceful manual shutdown) and other general `Exception`s that might occur during polling.
    - Ensures the scheduler is shut down in both KeyboardInterrupt and general exception cases to clean up resources.
            .
'''


if __name__ == '__main__':
    # This is the entry point, runs the synchronous main function
    main()