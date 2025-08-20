from services.github.token.get_installation_token import get_installation_access_token


OWNER = "gitautoai"
REPO = "gitauto"
FORKED_REPO = "DeepSeek-R1"
INSTALLATION_ID = 60314628
TOKEN = get_installation_access_token(installation_id=INSTALLATION_ID)
