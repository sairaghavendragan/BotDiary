from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import ContextTypes,ConversationHandler
from telegram.helpers import escape_markdown
from telegram.constants import ChatAction
import db
import datetime
from dateutil.parser import parse
from dateparser.search import search_dates
import scheduler
import pytz 
import utils
import gemini_client   

# Define states for the ConversationHandler
GEMINI_CONVERSATION = 0 # State for ongoing Gemini chat

 
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

async def add_new_todo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    user_id = db.get_or_create_user(chat_id)
    command_args = context.args
    if not command_args:
        await update.message.reply_text("Usage: `/todo [task]`\n\n"
            "Examples:\n"
            "`/todo Buy milk`\n" 
            "`/todo Call Mom`\n " 
            "`/todo Project deadline`", 
            parse_mode='Markdown' )    
        return
    todo = " ".join(command_args)
    todo = utils.escape_markdown_v1(todo)
    todo_id = db.add_todo(user_id, todo)
    await update.message.reply_text(f"Todo {todo_id} added: {todo}",parse_mode='Markdown') 
     

def _get_formatted_todos_content(user_id: int) -> tuple[str, InlineKeyboardMarkup | None]:
    """
    Generates the formatted TODO list message and its inline keyboard.
    Returns a tuple: (message_text: str, reply_markup: InlineKeyboardMarkup | None)
    """
    today = datetime.date.today()
    today_str = today.strftime('%Y-%m-%d')
    todos = db.get_todos_for_user(user_id, today_str)  
    response_text = f"📝 *Your TODOs for Today ({today.strftime('%Y-%m-%d')}):*\n\n"
    keyboard =[]
    if not todos:
        response_text += "No TODOs found for today. Use `/todo` to add a new TODO."
    else:  
        for todo in todos:
            status_emoji = "✅" if todo['is_done'] else "❌"
            task_display = todo['content'] 
             
            response_text += f"{status_emoji} {task_display} "
            buttons = []
            if not todo['is_done']:
                buttons.append(InlineKeyboardButton("✅ Done", callback_data=f"done:{todo['id']}"))
            else :
                buttons.append(InlineKeyboardButton("↩️ Undo", callback_data=f"undone:{todo['id']}"))    
            buttons.append(InlineKeyboardButton("Delete", callback_data=f"delete:{todo['id']}"))
            keyboard.append(buttons)
            response_text += "\n\n"

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    return response_text, reply_markup




async def _send_or_edit_todos(update: Update,context: ContextTypes.DEFAULT_TYPE, message_id: int=None) -> None:
     
    if update.message:
        chat_id = update.message.chat_id
    else:
        chat_id = update.callback_query.message.chat.id    
    user_id = db.get_or_create_user(chat_id)

    response_text, reply_markup = _get_formatted_todos_content(user_id)
    if message_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message_id,
            text=response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
async def show_daily_todos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
     
     
    await _send_or_edit_todos(update, context)        

async def handle_todo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer() # Acknowledge the callback query

    callback_data = query.data
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    user_id = db.get_or_create_user(chat_id) # Ensure user exists

    # Callback data format: "todo_[action]_[todo_id]"
    parts = callback_data.split(':')
    if len(parts) != 2:
        print(f"Invalid callback data: {callback_data}")
        return 
    action = parts[0]
    todo_id = int(parts[1])

    if action == 'done':
        db.mark_todo_done(todo_id, True)
    elif action == 'undone':
        db.mark_todo_done(todo_id, False)
    elif action == 'delete':
        db.delete_todo(todo_id)
    else:
        print(f"Unknown TODO action: {action}")
        return

    # After modification, re-render the TODO list by editing the original message
    await _send_or_edit_todos(update,context, message_id)

async def start_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point for the /gemini command.
    Checks if a query is provided for single-turn, or starts multi-turn.
    """
    chat_id = update.message.chat_id
    user_id = db.get_or_create_user(chat_id)
    query_text = " ".join(context.args) if context.args else None

    # Indicate typing while processing
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    if query_text:
        # Single-turn interaction
        print(f"User {user_id} sending single Gemini query: {query_text}")
        response_text = await gemini_client.send_single_query_to_gemini(query_text)
        
        if response_text == "No content generated.":
            await update.message.reply_text("🤖 Sorry, I couldn't get a response from Gemini right now. Please try again later.", parse_mode='Markdown')
        else:
            response_text = utils.markdown_to_safe_html(response_text)
            chunks = utils.split_message_for_telegram(response_text)
            chunks = utils.fix_chunks_with_tags(chunks)
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode='html')

        
        return ConversationHandler.END # End the conversation here as it's single-turn
    else:
        # Start multi-turn conversation
        print(f"User {user_id} starting multi-turn Gemini chat.")
        chat_session = gemini_client.start_new_gemini_chat()
        context.user_data['gemini_chat_session'] = chat_session
        
        await update.message.reply_text(
            "💬 *Gemini Chat started!* Send me your questions. Type `/endgemini` to end the chat.",
            parse_mode='Markdown'
        )
        return GEMINI_CONVERSATION # Transition to the conversation state

async def continue_gemini_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles messages during an ongoing Gemini chat session.
    """
    chat_id = update.message.chat_id
    user_id = db.get_or_create_user(chat_id)
    user_message = update.message.text 

    chat_session = context.user_data['gemini_chat_session']

    # Indicate typing while processing
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    print(f"User {user_id} continuing Gemini chat with: {user_message}")
    response_text = await gemini_client.send_message_to_gemini_chat(chat_session, user_message)

    if response_text == "No content generated.":
        await update.message.reply_text("🤖 Sorry, I couldn't get a response from Gemini right now. Please try again later.", parse_mode='Markdown')
    else:
        
        response_text = utils.markdown_to_safe_html(response_text)
        chunks = utils.split_message_for_telegram(response_text)
        chunks = utils.fix_chunks_with_tags(chunks)
        for chunk in chunks: 
            await update.message.reply_text(chunk, parse_mode='html')
             
        
    
    return GEMINI_CONVERSATION # Stay in the conversation state

async def end_gemini_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Ends the Gemini multi-turn conversation.
    """
    user_id = db.get_or_create_user(update.message.chat_id)
    print(f"User {user_id} ending multi-turn Gemini chat.")
    if 'gemini_chat_session' in context.user_data:
        del context.user_data['gemini_chat_session'] # Clear the session
    
    await update.message.reply_text("👋 *Gemini Chat ended.* You can start a new one with `/gemini`.", parse_mode='MarkdownV2')
    return ConversationHandler.END # End the conversation    