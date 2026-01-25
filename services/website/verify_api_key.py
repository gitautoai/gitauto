from fastapi import HTTPException

from constants.website import GITAUTO_API_KEY


def verify_api_key(api_key: str) -> None:
    """Verify the API key from the website."""
    if api_key != GITAUTO_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
