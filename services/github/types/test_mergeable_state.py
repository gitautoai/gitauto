from typing import get_args

from services.github.types.mergeable_state import MergeableState

# https://docs.github.com/en/graphql/reference/enums#mergestatestatus
EXPECTED_STATES = {
    "behind",
    "blocked",
    "clean",
    "dirty",
    "draft",
    "has_hooks",
    "unknown",
    "unstable",
}


def test_mergeable_state_values():
    assert set(get_args(MergeableState)) == EXPECTED_STATES
