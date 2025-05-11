from tests.constants import OWNER
from services.supabase.owners.get_owner import get_owner


def test_get_owner_success():
    owner_id = 159883862
    result = get_owner(owner_id)
    assert result is not None
    assert result["owner_id"] == owner_id
    assert result["owner_name"] == OWNER

def test_get_owner_not_found():
    result = get_owner(999999999)
    assert result is None