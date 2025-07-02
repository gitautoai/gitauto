from constants.urls import GH_BASE_URL
from services.github.types.owner import OwnerType


def create_permission_url(owner_type: OwnerType, owner_name: str, installation_id: int):
    url_part = f"settings/installations/{installation_id}/permissions/update"
    if owner_type == "Organization":
        return f"{GH_BASE_URL}/organizations/{owner_name}/{url_part}"
    return f"{GH_BASE_URL}/{url_part}"
