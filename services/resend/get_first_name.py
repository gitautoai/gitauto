import re
def get_first_name(user_name: str) -> str:
    """Extract first name from user_name field"""
    if not user_name:
        return "there"

    # Split by any whitespace (including all Unicode whitespace) and take the first part
    parts = [part for part in re.split(r'[\s\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\u200b]+', user_name.strip()) if part]
    if parts:
        return parts[0]

    return "there"
