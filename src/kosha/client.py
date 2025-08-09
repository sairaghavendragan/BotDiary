
from google import genai
from google.genai import types
from google.genai import chats

from .core.config import GEMINI_API_KEY

# Configure the generative AI client
client = genai.Client(api_key=GEMINI_API_KEY)

SAFETY_SETTINGS = [
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
]

MODEL_NAME = "gemini-2.5-flash"
CHAT_MODEL_NAME = "gemini-2.5-flash-lite"

async def get_summary(summary_prompt: str) -> str:
    """Generates a summary from a given prompt."""
    try:
        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=summary_prompt,
            config=types.GenerateContentConfig(safety_settings=SAFETY_SETTINGS),
        )
        return response.text or "No content generated."
    except Exception as e:
        print(f"Gemini API (Summary): An error occurred: {e}")
        return "No content generated."

def get_summary_prompt(content: str, summary_date: str) -> str:
    """Creates a standardized prompt for daily summary generation."""
    return f"""
    You are an AI assistant designed to summarize daily journal entries.
    Your goal is to provide a concise, insightful, and coherent summary of the provided text.
    Focus on key activities, significant thoughts, recurring themes, and notable events from the day.
    Keep the summary to around 3-5 concise paragraphs.

    Date: {summary_date}

    Journal Entries:
    ---
    {content}
    ---

    Please provide a summary of the above journal entries for the specified date.
    """

async def send_single_query_to_gemini(query_content: str) -> str:
    """Sends a single query to the Gemini chat model."""
    try:
        response = await client.aio.models.generate_content(
            model=CHAT_MODEL_NAME,
            contents=query_content,
            config=types.GenerateContentConfig(safety_settings=SAFETY_SETTINGS),
        )
        return response.text or "No content generated."
    except Exception as e:
        print(f"Gemini API (Single Query): An error occurred: {e}")
        return "No content generated."

def start_new_gemini_chat() -> chats.AsyncChat:
    """Starts a new multi-turn Gemini chat session."""
    return client.aio.chats.create(
        model=CHAT_MODEL_NAME,
        config=types.GenerateContentConfig(safety_settings=SAFETY_SETTINGS)
    )

async def send_message_to_gemini_chat(chat_session: chats.AsyncChat, message_content: str) -> str:
    """Sends a message within an ongoing Gemini chat session."""
    try:
        response = await chat_session.send_message(message=message_content)
        return response.text or "No content generated."
    except Exception as e:
        print(f"Gemini API (Multi-turn Chat): An error occurred: {e}")
        return "No content generated."
