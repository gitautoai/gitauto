import re

from utils.error.handle_exceptions import handle_exceptions

# Matches <style>...</style> and <script>...</script> blocks including their content
HTML_NOISE_RE = re.compile(r"<(style|script)\b[^>]*>[\s\S]*?</\1>", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<[^>]+>")


@handle_exceptions(default_return_value="", raise_on_error=False)
def strip_html(text: str):
    text = HTML_NOISE_RE.sub("", text)
    text = HTML_TAG_RE.sub("", text)
    # Collapse whitespace runs left after stripping tags
    text = re.sub(r"\n\s*\n", "\n", text).strip()
    return text
