import re


# Cross-ref: website/utils/parse-name.ts
def get_first_name(user_name: str) -> str:
    if not user_name:
        return "there"

    # Strip parenthesized content e.g. "John (Johnny) Doe" → "John Doe"
    cleaned = re.sub(r"\s*\([^)]*\)\s*", " ", user_name)
    parts = cleaned.strip().split()
    if not parts:
        return "there"

    # Skip title prefixes like "Dr." or initials like "L." when followed by an actual name
    idx = 1 if parts[0].endswith(".") and len(parts) > 1 else 0
    first = parts[idx]

    # Handle dot-separated tokens (e.g. "Frater.nul" → "Frater", "M.Rama" → "Rama")
    dot_parts = first.split(".")
    if len(dot_parts) > 1 and dot_parts[1]:
        first = max(dot_parts, key=len)

    # Single-token hyphenated names are firstname-lastname (e.g. "cuong-tran" → "cuong")
    # Multi-token keeps hyphens (e.g. "Mary-Jane Watson" → "Mary-Jane")
    if len(parts) == 1 and "-" in first:
        first = first.split("-")[0]

    # Names containing digits are likely GitHub usernames (e.g. "St119848"), not real names
    if not first or re.search(r"\d", first):
        return "there"

    return first[0].upper() + first[1:]
