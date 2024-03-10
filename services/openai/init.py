from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_ORG_ID


def create_openai_client() -> OpenAI:
    return OpenAI(api_key=OPENAI_API_KEY, organization=OPENAI_ORG_ID)
