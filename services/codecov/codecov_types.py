from typing import TypedDict


class CodecovTotals(TypedDict):
    files: int
    lines: int
    hits: int
    misses: int
    partials: int
    coverage: float
    branches: int
    methods: int
    messages: int
    sessions: int
    complexity: int
    complexity_total: int
    complexity_ratio: float
    diff: dict


class CodecovFile(TypedDict):
    name: str
    totals: CodecovTotals
    line_coverage: list[int]


class CodecovCommitResponse(TypedDict):
    totals: CodecovTotals
    files: list[CodecovFile]
    commit_file_url: str


class CodecovFileResult(TypedDict):
    name: str
    coverage: float
    uncovered_lines: list[int]
    partially_covered_lines: list[int]
