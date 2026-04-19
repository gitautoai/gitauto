from typing import Literal

# https://docs.github.com/en/graphql/reference/enums#mergestatestatus
MergeableState = Literal[
    "behind",
    "blocked",
    "clean",
    "dirty",
    "draft",
    "has_hooks",
    "unknown",
    "unstable",
]
