from dateparser.search import search_dates
import pytz
import datetime
import dotenv
import os
import re
import html

dotenv.load_dotenv()

TIMEZONE =os.getenv('TIMEZONE')  
tz = pytz.timezone(TIMEZONE)
now = datetime.datetime.now(tz)
def reminder_input(input_text):
    results = search_dates(input_text, settings={
    'TIMEZONE': TIMEZONE,
    'RETURN_AS_TIMEZONE_AWARE': True,
    'PREFER_DATES_FROM': 'future',
    'RELATIVE_BASE': datetime.datetime.now(tz)
})

    if not results:
        print("No date/time found in:", input_text)
        return None,""

    time_str, parsed_datetime = results[0]
    reminder_message = input_text.replace(time_str, "").strip()
     

    return parsed_datetime,reminder_message

def parse_datetime(input_text):
    results = search_dates(input_text, settings={
    'TIMEZONE': TIMEZONE,
    'RETURN_AS_TIMEZONE_AWARE': True,
    'PREFER_DATES_FROM': 'past',
    'RELATIVE_BASE': datetime.datetime.now(tz)
})

    if not results:
        print("No date/time found in:", input_text)
        return None

    _, parsed_datetime = results[0]
    return parsed_datetime

def  normalize_timestamp(timestamp ) -> datetime:
    """ 
    If already aware, it converts it to the app's timezone.
    """
     
    
    if timestamp.tzinfo is None:
        return tz.localize(timestamp)
    else:
        return timestamp.astimezone(tz)    
    
def escape_markdown_v1(text: str) -> str:
    for ch in ['_', '*', '`', '[']:
        text = text.replace(ch, f'\\{ch}')
    return text    

def split_message_for_telegram(text: str, max_length: int = 4000) -> list[str]:
    chunks = []
    current_chunk = []
    current_length = 0

    paragraphs = text.split('\n\n')

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if current_length + len(para) + 2 > max_length:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_length = 0

            if len(para) > max_length:
                lines = para.split('\n')
                for line in lines:
                    line = line.strip()
                    if current_length + len(line) + 1 > max_length:
                        if current_chunk:
                            chunks.append('\n'.join(current_chunk))
                            current_chunk = []
                            current_length = 0
                    current_chunk.append(line)
                    current_length += len(line) + 1
            else:
                current_chunk.append(para)
                current_length += len(para) + 2
        else:
            current_chunk.append(para)
            current_length += len(para) + 2

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks

 

# List of tags  to track for chunk boundary fixes
 
TRACKED_TAGS = ['pre', 'code', 'b', 'i', 'u', 'strong', 'em']

# Regex patterns for opening and closing tags of tracked tags
OPEN_TAG_RE = re.compile(r'<({})>'.format('|'.join(TRACKED_TAGS)))
CLOSE_TAG_RE = re.compile(r'</({})>'.format('|'.join(TRACKED_TAGS)))

def get_open_tags(text: str) -> list[str]:
    """
    Parse the text and return a list of open tags (that have no corresponding closing tag).
    It only tracks the tags in TRACKED_TAGS list.
    """
    stack = []
    # Find all tags in order (open or close)
    tags = re.findall(r'</?(\w+)>', text)
    
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower not in TRACKED_TAGS:
            continue
        
        # Check if it is closing tag or opening tag
         

    # Let's do a proper finditer to track tags in order:
    stack.clear()
    for match in re.finditer(r'</?(\w+)>', text):
        full_tag = match.group(0)
        tag_name = match.group(1).lower()
        if tag_name not in TRACKED_TAGS:
            continue
        if full_tag.startswith('</'):  # closing tag
            if stack and stack[-1] == tag_name:
                stack.pop()
            else:
                # Closing tag without matching open, ignore or remove
                # We'll ignore here
                pass
        else:  # opening tag
            stack.append(tag_name)
    return stack


def fix_chunks_with_tags(chunks: list[str]) -> list[str]:
    """
    For each chunk except the last,
    append closing tags for all currently open tags at the end,
    and prepend those opening tags to the next chunk.
    """
    fixed_chunks = chunks.copy()
    for i in range(len(fixed_chunks) - 1):
        open_tags = get_open_tags(fixed_chunks[i])
        if not open_tags:
            continue
        
        # Close tags in reverse order at the end of current chunk
        closing_tags = ''.join(f'</{tag}>' for tag in reversed(open_tags))
        fixed_chunks[i] += closing_tags
        
        # Add opening tags in order at the start of next chunk
        opening_tags = ''.join(f'<{tag}>' for tag in open_tags)
        fixed_chunks[i + 1] = opening_tags + fixed_chunks[i + 1]
    
    return fixed_chunks



def markdown_to_safe_html(text: str) -> str:
    # Escape HTML-sensitive characters
    text = html.escape(text)

    # Convert bold **text** to <b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    # Convert italic *text* to <i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)

    # Convert inline code `code` to <code>
    text = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', text)

    # Convert multiline code blocks ```...``` to <pre>
    text = re.sub(r'&lt;pre&gt;.*?&lt;/pre&gt;', '', text)  # remove nested pre if any
    text = re.sub(r'```(.*?)```', lambda m: f"<pre>{html.escape(m.group(1))}</pre>", text, flags=re.DOTALL)

    return text




 