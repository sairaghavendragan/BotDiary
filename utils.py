from dateparser.search import search_dates
import pytz
import datetime
import dotenv
import os

dotenv.load_dotenv()

TIMEZONE =os.getenv('TIMEZONE')  
tz = pytz.timezone(TIMEZONE)
now = datetime.datetime.now(tz)
def reminder_input(input_text):
    results = search_dates(input_text, settings={
    'TIMEZONE': TIMEZONE,
    'RETURN_AS_TIMEZONE_AWARE': True,
    'PREFER_DATES_FROM': 'future',
    'RELATIVE_BASE': now
})

    if not results:
        print("No date/time found in:", input_text)
        return

    time_str, parsed_datetime = results[0]
    reminder_message = input_text.replace(time_str, "").strip()

    return parsed_datetime,reminder_message

    print(f"Input: {input_text}")
    print(f"Parsed time phrase: {time_str}")
    print(f"Datetime (tz-aware): {parsed_datetime}")
    print(f"Reminder message: {reminder_message}")
    print("-" * 40)

 