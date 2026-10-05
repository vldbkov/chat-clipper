# Clipboard reader module (cross-platform via platform_utils)
from platform_utils import get_clipboard_text, get_clipboard_html


# Read plain text from clipboard
def get_text() -> str:
    return get_clipboard_text()


# Read text and HTML from clipboard
# Returns tuple (plain_text, html_text). html_text may be empty string
def get_text_with_format() -> tuple:
    plain = get_clipboard_text()
    html = get_clipboard_html()
    return plain, html