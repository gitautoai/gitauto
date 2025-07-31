import re
def get_first_name(user_name: str) -> str:
    """Extract first name from user_name field"""
    if not user_name:
        return "there"

    # Split by any whitespace (including all Unicode whitespace) and take the first part
    parts = [part for part in re.split(r'\s+', user_name.strip()) if part]
    if parts:
        return parts[0]

    return "there"
