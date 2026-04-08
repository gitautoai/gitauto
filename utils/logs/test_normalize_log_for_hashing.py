from utils.logs.normalize_log_for_hashing import normalize_log_for_hashing

# Two real raw error logs from nebula-crm PR #1 (usage IDs 14971 and 14972). Same underlying error (missing UX evidence file) but different commit SHAs because GitAuto created empty commits between runs.
RAW_LOG_RUN_A = """```GitHub Check Run Log: frontend-ui/3_Validate frontend UX evidence.txt
 ##[group]Run set -euo pipefail
set -euo pipefail
if [[ "pull_request" == "pull_request" ]]; then
  python3 agents/frontend-developer/scripts/validate-frontend-ux-evidence.py \\
    --base "22ce64161c5e231ee05a34c2bbb124655c9dabbc" \\
    --head "84c1d81d16d948a860942a215a564d4ea917d965"
elif [[ "pull_request" == "push" ]]; then
  python3 agents/frontend-developer/scripts/validate-frontend-ux-evidence.py \\
    --base "736b80f04e412839d3eaa2782db6180e63de2600" \\
    --head "84c1d81d16d948a860942a215a564d4ea917d965"
else
  python3 agents/frontend-developer/scripts/validate-frontend-ux-evidence.py
fi
shell: /usr/bin/bash -e {0}
##[endgroup]
Frontend UX evidence validation
------------------------------------------------------------
[Range] 22ce64161c5e231ee05a34c2bbb124655c9dabbc..84c1d81d16d948a860942a215a564d4ea917d965
[Info] Frontend UI files changed:
  - experience/src/features/opportunities/tests/StageNodeStoryPanel.test.tsx
2026-03-20T15:58:04.7920475Z

[FAIL] Frontend UI changed but no UX evidence file was updated.
Add an evidence file under:
  planning-mds/operations/evidence/frontend-ux/ux-audit-YYYY-MM-DD.md
Template:
  planning-mds/operations/evidence/frontend-ux/TEMPLATE.md
##[error]Process completed with exit code 1.
```"""

# Same log but after GA created an empty commit, so only the head SHA and timestamps changed
RAW_LOG_RUN_B = """```GitHub Check Run Log: frontend-ui/3_Validate frontend UX evidence.txt
 ##[group]Run set -euo pipefail
set -euo pipefail
if [[ "pull_request" == "pull_request" ]]; then
  python3 agents/frontend-developer/scripts/validate-frontend-ux-evidence.py \\
    --base "22ce64161c5e231ee05a34c2bbb124655c9dabbc" \\
    --head "0ddf0ab35562404576d6a02dc94bf2c859577b57"
elif [[ "pull_request" == "push" ]]; then
  python3 agents/frontend-developer/scripts/validate-frontend-ux-evidence.py \\
    --base "c8a6409bd87861d0779d8d85afb445ae26729c4a" \\
    --head "0ddf0ab35562404576d6a02dc94bf2c859577b57"
else
  python3 agents/frontend-developer/scripts/validate-frontend-ux-evidence.py
fi
shell: /usr/bin/bash -e {0}
##[endgroup]
Frontend UX evidence validation
------------------------------------------------------------
[Range] 22ce64161c5e231ee05a34c2bbb124655c9dabbc..0ddf0ab35562404576d6a02dc94bf2c859577b57
[Info] Frontend UI files changed:
  - experience/src/features/opportunities/tests/StageNodeStoryPanel.test.tsx
2026-03-20T15:59:44.3578893Z

[FAIL] Frontend UI changed but no UX evidence file was updated.
Add an evidence file under:
  planning-mds/operations/evidence/frontend-ux/ux-audit-YYYY-MM-DD.md
Template:
  planning-mds/operations/evidence/frontend-ux/TEMPLATE.md
##[error]Process completed with exit code 1.
```"""


def test_same_error_different_shas_produce_same_normalized_output():
    normalized_a = normalize_log_for_hashing(RAW_LOG_RUN_A)
    normalized_b = normalize_log_for_hashing(RAW_LOG_RUN_B)
    assert normalized_a == normalized_b


def test_shas_are_replaced_in_real_log():
    result = normalize_log_for_hashing(RAW_LOG_RUN_A)
    assert "84c1d81d16d948a860942a215a564d4ea917d965" not in result
    assert "22ce64161c5e231ee05a34c2bbb124655c9dabbc" not in result
    assert "<SHA>" in result


def test_preserves_error_message_in_real_log():
    result = normalize_log_for_hashing(RAW_LOG_RUN_A)
    assert "[FAIL] Frontend UI changed but no UX evidence file was updated." in result
    assert (
        "planning-mds/operations/evidence/frontend-ux/ux-audit-YYYY-MM-DD.md" in result
    )


def test_empty_string():
    assert normalize_log_for_hashing("") == ""
