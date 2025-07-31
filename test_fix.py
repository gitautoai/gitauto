import re

def get_first_name(user_name: str) -> str:
    """Extract first name from user_name field"""
    if not user_name:
        return "there"

    # Include standard whitespace plus common Unicode whitespace characters
    whitespace_pattern = r'[\s\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\u200b\u200c\u200d\u2060\ufeff]+'
    parts = [part for part in re.split(whitespace_pattern, user_name.strip()) if part]
    if parts:
        return parts[0]
    return "there"

print(repr(get_first_name("John\u200b Doe")))  # Should print 'John'