from google import genai

from constants.google_ai import GOOGLE_AI_API_KEY
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def get_google_ai_client():
    return genai.Client(api_key=GOOGLE_AI_API_KEY)
