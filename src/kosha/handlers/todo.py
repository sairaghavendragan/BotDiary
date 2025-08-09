import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .auth import restricted_access
from .. import db, utils


def _get_formatted_todos_content(user_id: int) -> tuple[str, InlineKeyboardMarkup | None]:
    """Generates the formatted TODO list message and its inline keyboard."""
    today = datetime.date.today()
    todos = db.get_todos_for_user(user_id, today.strftime('%Y-%m-%d'))
    
    response_text = f"📝 *Your TODOs for Today ({today.strftime('%Y-%m-%d')}):*\n\n"
    keyboard = []
    
    if not todos:
        response_text += "No TODOs found for today. Use `/todo` to add one."
    else:
        for todo in todos:
            status_emoji = "✅" if todo['is_done'] else "❌"
            task_display = todo['content']
            response_text += f"{status_emoji} {task_display} \n\n"
            
            buttons = []
            if not todo['is_done']:
                buttons.append(InlineKeyboardButton("✅ Done", callback_data=f"done:{todo['id']}"))
            else:
                buttons.append(InlineKeyboardButton("↩️ Undo", callback_data=f"undone:{todo['id']}"))
            buttons.append(InlineKeyboardButton("Delete", callback_data=f"delete:{todo['id']}"))
            keyboard.append(buttons)

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    return response_text, reply_markup


async def _send_or_edit_todos(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int = None) -> None:
    """Sends or edits the TODO list message."""
    if not update.effective_chat:
        return
        
    user_id = db.get_or_create_user(update.effective_chat.id)
    response_text, reply_markup = _get_formatted_todos_content(user_id)
    
    if message_id and context.bot:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message_id,
            text=response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif update.message:
        await update.message.reply_text(
            text=response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

@restricted_access
async def add_new_todo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adds a new TODO item."""
    if not update.message or not context.args:
        await update.message.reply_text("Usage: /todo [task description]")
        return

    user_id = db.get_or_create_user(update.message.chat_id)
    todo_text = " ".join(context.args)
    escaped_todo = utils.escape_markdown_v1(todo_text)
    
    db.add_todo(user_id, escaped_todo)
    await _send_or_edit_todos(update, context)

@restricted_access
async def show_daily_todos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the TODO list for the current day."""
    await _send_or_edit_todos(update, context)

@restricted_access
async def handle_todo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button presses on the TODO list."""
    query = update.callback_query
    if not query or not query.data or not query.message:
        return
        
    await query.answer()

    action, _, todo_id_str = query.data.partition(':')
    todo_id = int(todo_id_str)

    if action == 'done':
        db.mark_todo_done(todo_id, True)
    elif action == 'undone':
        db.mark_todo_done(todo_id, False)
    elif action == 'delete':
        db.delete_todo(todo_id)
    else:
        print(f"Unknown TODO action: {action}")
        return

    await _send_or_edit_todos(update, context, message_id=query.message.message_id)
