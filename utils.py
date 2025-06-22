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
        return None,""

    time_str, parsed_datetime = results[0]
    reminder_message = input_text.replace(time_str, "").strip()
     

    return parsed_datetime,reminder_message

def  normalize_timestamp(timestamp ) -> datetime:
    """ 
    If already aware, it converts it to the app's timezone.
    """
     
    
    if timestamp.tzinfo is None:
        return tz.localize(timestamp)
    else:
        return timestamp.astimezone(tz)    

 