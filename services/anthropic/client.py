from anthropic import Anthropic

from constants.claude import CLAUDE_API_KEY

# Set timeout to 9 minutes (540 seconds) to avoid "ValueError: Streaming is strongly recommended for operations that may take longer than 10 minutes" error
claude = Anthropic(api_key=CLAUDE_API_KEY, timeout=540.0)
