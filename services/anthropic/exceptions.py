class ClaudeOverloadedError(Exception):
    """Raised when Claude API returns 529 Overloaded error"""


class ClaudeAuthenticationError(Exception):
    """Raised when Claude API returns 401 Authentication error"""
