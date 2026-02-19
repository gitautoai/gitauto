from typing import TypedDict


class _Position(TypedDict):
    line: int
    column: int


class _Location(TypedDict):
    start: _Position


class _StatementEntry(TypedDict):
    start: _Position


class _FnEntry(TypedDict):
    name: str
    loc: _Location


class _BranchEntry(TypedDict):
    type: str
    loc: _Location
    locations: list[_Location]


class IstanbulFileCoverage(TypedDict):
    s: dict[str, int]
    f: dict[str, int]
    b: dict[str, list[int]]
    statementMap: dict[str, _StatementEntry]
    fnMap: dict[str, _FnEntry]
    branchMap: dict[str, _BranchEntry]
