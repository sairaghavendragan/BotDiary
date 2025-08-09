
import sys
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)

 
#append src directory to path so that modules can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.kosha.core import config
from src.kosha import db, scheduler
from src.kosha.handlers import general, reminders, todo, gemini

async def post_init(application: Application) -> None:
    """Post-initialization hook for the application."""
    print("Running post-initialization tasks...")
    try:
        scheduler.scheduler.start()
        print("Scheduler started.")
        await scheduler.setup_scheduler_jobs(application.bot)
        print("Scheduled jobs loaded.")
    except Exception as e:
        print(f"Error during post-initialization: {e}")

def main() -> None:
    """Set up and run the bot."""
    db.init_db()
    print("Database initialized.")

    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()

    # --- Conversation Handlers ---
    gemini_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("gemini", gemini.start_gemini)],
        states={
            gemini.GEMINI_CONVERSATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, gemini.continue_gemini_chat),
            ]
        },
        fallbacks=[
            CommandHandler("endgemini", gemini.end_gemini_conversation),

            # You can add other commands here to act as fallbacks
        ],
        allow_reentry=True
    )

    # --- Command and Message Handlers ---
    application.add_handler(gemini_conv_handler)
    application.add_handler(CommandHandler('remind', reminders.set_reminder))
    application.add_handler(CommandHandler('todo', todo.add_new_todo))
    application.add_handler(CommandHandler('todos', todo.show_daily_todos))
    application.add_handler(CommandHandler('summary', general.get_specific_summary))
    application.add_handler(CommandHandler('logs', general.show_logs))
    application.add_handler(CallbackQueryHandler(todo.handle_todo_callback))
    
    # This handler must be added last
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, general.handle_any_message))

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

 


if __name__ == '__main__':
    # This is the entry point, runs the synchronous main function
    main()
