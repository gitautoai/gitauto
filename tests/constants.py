from services.github.github_manager import get_installation_access_token


OWNER = "gitautoai"
REPO = "gitauto"
INSTALLATION_ID = 53743403
TOKEN = get_installation_access_token(installation_id=INSTALLATION_ID)
