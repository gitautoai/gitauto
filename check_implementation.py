# Let's check what the current implementation looks like
with open('services/resend/get_first_name.py', 'r') as f:
    content = f.read()
    print("Current implementation:")
    print(content)
    print("\n" + "="*50 + "\n")

# Test the specific failing case
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