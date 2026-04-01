# Standard imports
import json

# Local imports
from utils.prompts.base_role import BASE_ROLE
from utils.quality_checks.checklist import QUALITY_CHECKLIST

QUALITY_CHECK_SYSTEM_PROMPT = f"""{BASE_ROLE}

## Checklist
{json.dumps(QUALITY_CHECKLIST, indent=2)}

## Instructions
For each category and each check, evaluate whether the test file rigorously covers that check for the given source file.

Return a JSON object with this exact structure - every category and every check from the checklist above must be present:
{{
  "category_name": {{
    "check_name": {{
      "status": "pass" | "fail" | "na",
      "reason": "Concise reason (required for fail, optional for pass/na)"
    }}
  }}
}}

## Grading standards
- "pass": The test file has EXPLICIT, TARGETED tests for this check. A test that coincidentally covers a case does not count. The test must demonstrate intent to verify this specific behavior.
- "fail": The check is relevant to this source file AND the test file either (a) does not test it at all, (b) tests it superficially without edge cases, or (c) only tests the happy path without adversarial inputs. Mediocre or shallow coverage is a fail.
- "na": This check is genuinely not applicable to this source file type (e.g. SEO checks for a utility function, CSRF for a pure function with no HTTP context).

Mark "na" generously for checks that genuinely don't apply to the file type. But for every applicable check, demand rigorous, intentional test coverage. If in doubt between pass and fail, mark fail."""
