from dateparser.search import search_dates
import pytz
import datetime
import re
import html

from .core.config import TIMEZONE

tz = pytz.timezone(TIMEZONE)

def reminder_input(input_text):
    """Parses a string to find a date and a reminder message."""
    now = datetime.datetime.now(tz)
    results = search_dates(input_text, settings={
        'TIMEZONE': TIMEZONE,
        'RETURN_AS_TIMEZONE_AWARE': True,
        'PREFER_DATES_FROM': 'future',
        'RELATIVE_BASE': now
    })

    if not results:
        return None, ""

    time_str, parsed_datetime = results[0]
    reminder_message = input_text.replace(time_str, "").strip()
    return parsed_datetime, reminder_message

def parse_datetime(input_text):
    """Parses a string to find a single date."""
    now = datetime.datetime.now(tz)
    results = search_dates(input_text, settings={
        'TIMEZONE': TIMEZONE,
        'RETURN_AS_TIMEZONE_AWARE': True,
        'PREFER_DATES_FROM': 'past',
        'RELATIVE_BASE': now
    })
    return results[0][1] if results else None

def normalize_timestamp(timestamp: datetime.datetime) -> datetime.datetime:
    """Converts a timestamp to the application's configured timezone."""
    if timestamp.tzinfo is None:
        return tz.localize(timestamp)
    else:
        return timestamp.astimezone(tz)

def escape_markdown_v1(text: str) -> str:
    """Escapes characters for Telegram's Markdown v1."""
    for char in ['_', '*', '`', '[']:
        text = text.replace(char, f'\\{char}')
    return text

def split_message_for_telegram(text: str, max_length: int = 4000) -> list[str]:
    """Splits a long message into chunks suitable for Telegram."""
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
            
            # Further split very long paragraphs
            if len(para) > max_length:
                lines = para.split('\n')
                for line in lines:
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


TRACKED_TAGS = ['pre', 'code', 'b', 'i', 'u', 'strong', 'em']

def get_open_tags(text: str) -> list[str]:
    """Finds unclosed HTML tags from a predefined list."""
    stack = []
    for match in re.finditer(r'</?(\w+)>', text):
        tag_name = match.group(1).lower()
        if tag_name not in TRACKED_TAGS:
            continue
        if match.group(0).startswith('</'):
            if stack and stack[-1] == tag_name:
                stack.pop()
        else:
            stack.append(tag_name)
    return stack

def fix_chunks_with_tags(chunks: list[str]) -> list[str]:
    """Ensures HTML tags are properly closed and reopened across message chunks."""
    fixed_chunks = list(chunks)
    open_tags_stack = []
    for i, chunk in enumerate(fixed_chunks):
        # Add tags that were open from the previous chunk
        if open_tags_stack:
            opening_tags = ''.join(f'<{tag}>' for tag in open_tags_stack)
            fixed_chunks[i] = opening_tags + chunk

        open_tags_stack = get_open_tags(fixed_chunks[i])

        # Close any remaining open tags at the end of the chunk
        if open_tags_stack and i < len(fixed_chunks) - 1:
            closing_tags = ''.join(f'</{tag}>' for tag in reversed(open_tags_stack))
            fixed_chunks[i] += closing_tags

    return fixed_chunks

def markdown_to_safe_html(text: str) -> str:
    """Converts basic Markdown to Telegram-safe HTML."""
    text = html.escape(text)
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Italic
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Inline code
    text = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', text)
    # Code blocks
    text = re.sub(r'```(.*?)```', lambda m: f'<pre>{html.escape(m.group(1))}</pre>', text, flags=re.DOTALL)
    return text