
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ChatAction

from .auth import restricted_access
from .. import db, utils, client as gemini_client

# Define state for the conversation
GEMINI_CONVERSATION = 0

@restricted_access
async def start_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the /gemini command."""
    if not update.message:
        return ConversationHandler.END

    chat_id = update.message.chat_id
    user_id = db.get_or_create_user(chat_id)
    query_text = " ".join(context.args) if context.args else None

    if context.bot:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    if query_text:
        # Single-turn interaction
        print(f"User {user_id} sending single Gemini query: {query_text}")
        response_text = await gemini_client.send_single_query_to_gemini(query_text)
        
        if response_text == "No content generated.":
            await update.message.reply_text("🤖 Sorry, I couldn't get a response from Gemini.")
        else:
            response_text = utils.markdown_to_safe_html(response_text)
            chunks = utils.split_message_for_telegram(response_text)
            chunks = utils.fix_chunks_with_tags(chunks)
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode='html')
        
        return ConversationHandler.END
    else:
        # Start multi-turn conversation
        print(f"User {user_id} starting multi-turn Gemini chat.")
        chat_session = gemini_client.start_new_gemini_chat()
        context.user_data['gemini_chat_session'] = chat_session
        
        await update.message.reply_text(
            "💬 *Gemini Chat started!* Send me your questions. Type `/endgemini` to end the chat.",
            parse_mode='Markdown'
        )
        return GEMINI_CONVERSATION

@restricted_access
async def continue_gemini_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles messages during an ongoing Gemini chat session."""
    if not update.message or not update.message.text or not context.user_data:
        return GEMINI_CONVERSATION # Or END?

    chat_id = update.message.chat_id
    user_id = db.get_or_create_user(chat_id)
    user_message = update.message.text
    chat_session = context.user_data.get('gemini_chat_session')

    if not chat_session:
        await update.message.reply_text("Your chat session has expired. Please start a new one with /gemini.")
        return ConversationHandler.END

    if context.bot:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    print(f"User {user_id} continuing Gemini chat with: {user_message}")
    response_text = await gemini_client.send_message_to_gemini_chat(chat_session, user_message)

    if response_text == "No content generated.":
        await update.message.reply_text("🤖 Sorry, I couldn't get a response from Gemini.")
    else:
        response_text = utils.markdown_to_safe_html(response_text)
        chunks = utils.split_message_for_telegram(response_text)
        chunks = utils.fix_chunks_with_tags(chunks)
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode='html')
            
    return GEMINI_CONVERSATION

@restricted_access
async def end_gemini_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ends the Gemini multi-turn conversation."""
    if not update.message:
        return ConversationHandler.END

    user_id = db.get_or_create_user(update.message.chat_id)
    print(f"User {user_id} ending multi-turn Gemini chat.")
    
    if 'gemini_chat_session' in context.user_data:
        del context.user_data['gemini_chat_session']
    
    await update.message.reply_text("👋 *Gemini Chat ended.*", parse_mode='Markdown')
    return ConversationHandler.END
