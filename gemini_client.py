from google import genai
from google.genai import types
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

    import asyncio
    asyncio.run(test_summary())