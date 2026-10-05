# HTML to docx conversion via html4docx library
from html4docx import HtmlToDocx

from logger import log


# Convert HTML string to a docx Document
# Returns HtmlToDocx instance (inherits from Document) or None on failure
def convert(html_text: str):
    if not html_text or not html_text.strip():
        return None
    try:
        parser = HtmlToDocx()
        parser.parse_html_string(html_text)
        return parser
    except Exception as e:
        log.exception("html_to_docx.convert error: %s", e)
        return None