from google import genai
from google.genai import types
from google.genai import chats
import os
from dotenv import load_dotenv

load_dotenv() 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")


client = genai.Client ( api_key= GEMINI_API_KEY
)

SAFETY_SETTINGS = [
     
    types.SafetySetting(category= "HARM_CATEGORY_HATE_SPEECH", threshold= "BLOCK_NONE"),
    #types.SafetySetting(category="HARM_CATEGORY_HARRASSMENT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
]
MODEL_NAME = "gemini-2.5-flash"


CHAT_MODEL_NAME = "gemini-2.5-flash-lite"
 
async def get_summary(summary_prompt):
    try:
        response = await client.aio.models.generate_content(
                model=MODEL_NAME, # Model name is passed as an argument
                contents=summary_prompt,
                config=types.GenerateContentConfig( # Pass settings via the config object
                    safety_settings=SAFETY_SETTINGS,
                ),
            )
        if hasattr(response,"text") and response.text:
            return response.text
        else:
            print(f"Gemini API: No text content found in response. Raw response: {response}")
            return "No content generated."
    except Exception as e:  
        print(f"Gemini API: An error occurred: {e}")
        return "No content generated."

def get_summary_prompt(content,summary_date):
    prompt = f"""
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
    return prompt


async def send_single_query_to_gemini(query_content: str) -> str:
    """
    Sends a single query to the Gemini chat model without maintaining a session.
    Uses default safety settings.
    """
    try:
        response = await client.aio.models.generate_content(
                model=CHAT_MODEL_NAME, # Model name is passed as an argument
                contents=query_content,
                config=types.GenerateContentConfig( # Pass settings via the config object
                    safety_settings=SAFETY_SETTINGS,
                ),
            )
        if hasattr(response,"text") and response.text:
            return response.text
        else:
            print(f"Gemini API: No text content found in response. Raw response: {response}")
            return "No content generated."
    except Exception as e:  
        print(f"Gemini API: An error occurred: {e}")
        return "No content generated."
def start_new_gemini_chat() -> chats.AsyncChat:  
    """
    Starts a new multi-turn Gemini chat session.
    """
    chat = client.aio.chats.create(model=CHAT_MODEL_NAME,config=types.GenerateContentConfig(safety_settings=SAFETY_SETTINGS))
     
     
    return chat

async def send_message_to_gemini_chat(chat_session: chats.AsyncChat, message_content: str) -> str:
    """
    Sends a message within an ongoing Gemini chat session and gets the response.
    """
    try:
        response = await chat_session.send_message(
            message=message_content
        )
        if hasattr(response, "text") and response.text:
            return response.text
        else:
            print(f"Gemini API (Multi-turn Chat): No text content found in response. Raw response: {response}")
            return "No content generated."
    except Exception as e:
        print(f"Gemini API (Multi-turn Chat): An error occurred: {e}")
        # Potentially inspect e to see if it's a blocked content error
        return "No content generated."

if __name__ == "__main__":
    async def test_summary():
        if not GEMINI_API_KEY:
            print("GEMINI_API_KEY not set. Cannot run test.")
            return

        test_logs = """
        10:00: Started working on the bot diary project.
        11:30: Had a quick call with Sarah about the upcoming presentation.
        13:00: Lunch break. Made a sandwich.
        14:00: Debugged an issue with the reminder scheduler. Took longer than expected.
        17:00: Finished coding for the day. Feeling productive.
        """
        test_date = "2023-10-27"
        test_prompt = get_summary_prompt(test_logs, test_date)
        print("--- Generated Prompt ---")
        print(test_prompt)
        print("\n--- Gemini Response ---")
        summary = await get_summary(test_prompt)
        print(summary)
    async def test_gemini_chat_interaction():
        if not GEMINI_API_KEY:
            print("GEMINI_API_KEY not set. Cannot run test.")
            return

        print("\n--- Testing Single Query (1.5-flash) ---")
        single_query_response = await send_single_query_to_gemini("What is the capital of France?")
        print(f"Response: {single_query_response}")

        print("\n--- Testing Multi-turn Chat (1.5-flash) ---")
        chat_session = start_new_gemini_chat()
        print("Chat session started. Sending first message.")
        response1 = await send_message_to_gemini_chat(chat_session, "Tell me about the history of artificial intelligence.")
        print(f"Response 1: {response1}")

        print("Sending follow-up message.")
        response2 = await send_message_to_gemini_chat(chat_session, "What are some of its key milestones?")
        print(f"Response 2: {response2}")
    import asyncio
    asyncio.run(test_summary())
    asyncio.sleep(2)
    asyncio.run(test_gemini_chat_interaction())