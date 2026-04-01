from pathlib import Path

from constants.files import (
    TEST_DIR_NAMES,
    TEST_NAMING_PATTERNS,
    TEST_QUALIFIER_STRIP,
    TEST_SUPPORT_PATTERNS,
)
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_test_file import is_test_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=[], raise_on_error=False)
def find_test_files(
    impl_file_path: str,
    all_file_paths: list[str],
    test_dir_prefixes: list[str] | None,
):
    """Find test files for an implementation file using exact stem match + directory relationship.

    Two-step approach:
    1. Filter all_file_paths with is_test_file (cheap, no I/O)
    2. Exact stem match + directory relationship (cheap, no I/O)

    Returns all matches (not just first). Callers can optionally verify via import analysis
    by reading the returned candidates' content.

    Directory matching rules:
    1. Same directory (colocated): src/utils/generateId.test.ts
    2. Child test subdirectory: src/models/__tests__/Quote.test.ts
    3. Mirror directory: test/spec/services/getPolicyInfo.test.ts for src/services/getPolicyInfo.ts
    """
    impl_stem = Path(impl_file_path).stem.lower()
    if not impl_stem:
        logger.warning("Could not extract stem from: %s", impl_file_path)
        return list[str]()

    # e.g. "src/utils" for "src/utils/generateId.ts"
    impl_dir = str(Path(impl_file_path).parent).lower()

    # e.g. {"src/utils/__tests__", "src/utils/tests", ...} for child subdir matching
    child_test_dirs = {f"{impl_dir}/{d}" for d in TEST_DIR_NAMES}

    matches: list[str] = []
    for fp in all_file_paths:
        # Skip the impl file itself from candidate list
        if fp == impl_file_path:
            continue

        # Not a test file, skip (is_test_file logs internally)
        if not is_test_file(fp):
            continue

        fp_lower = fp.lower()
        if any(p.search(fp_lower) for p in TEST_SUPPORT_PATTERNS):
            logger.info("Skipping %s: not a real test (mock/fixture/snapshot)", fp)
            continue

        test_base_stem = Path(fp).stem
        for p in TEST_NAMING_PATTERNS:
            stripped = p.stem_strip.sub("", test_base_stem)  # pylint: disable=no-member
            if stripped != test_base_stem:
                # Found naming convention. Only apply first match to avoid double-stripping.
                # e.g. "test_utils" -> "utils", "Quote.spec" -> "Quote"
                logger.info("%s uses %s naming, impl stem: %s", fp, p.name, stripped)
                test_base_stem = stripped
                break

        # Without this, "disable-schedules.integration" won't match impl stem "disable-schedules"
        # e.g. "disable-schedules.integration" -> "disable-schedules", "disable-schedules" -> no-op
        test_base_stem = TEST_QUALIFIER_STRIP.sub("", test_base_stem)
        test_base_stem = test_base_stem.lower()
        # Most test files won't match — different impl file (too noisy to log)
        if test_base_stem != impl_stem:
            continue

        # e.g. "src/utils" for "src/utils/generateId.test.ts"
        test_dir = str(Path(fp).parent).lower()

        # e.g. src/utils/generateId.ts and src/utils/generateId.test.ts
        if test_dir == impl_dir:
            logger.info("Found test %s for %s (colocated)", fp, impl_file_path)
            matches.append(fp)
            continue

        # e.g. src/models/Quote.tsx and src/models/__tests__/Quote.test.ts
        if test_dir in child_test_dirs:
            logger.info("Found test %s for %s (child test dir)", fp, impl_file_path)
            matches.append(fp)
            continue

        test_parts = test_dir.split("/")
        impl_parts = impl_dir.split("/")

        # Custom test dir prefixes from DB (e.g. "tests/php/unit" for SPIDERPLUS).
        # Strip the prefix and compare remaining path with impl dir.
        prefix_matched = False
        for tdp in test_dir_prefixes or []:
            tdp_lower = tdp.lower().rstrip("/")

            # e.g. test file directly in tests/php/unit/ (no subdirectory)
            if test_dir == tdp_lower:
                logger.info(
                    "Found test %s for %s (directly in prefix root %s)",
                    fp,
                    impl_file_path,
                    tdp,
                )
                matches.append(fp)
                prefix_matched = True
                break

            # This prefix doesn't apply to this test dir
            if not test_dir.startswith(tdp_lower + "/"):
                continue

            remainder = test_dir[len(tdp_lower) + 1 :]

            # e.g. tests/php/unit/app/Services/ -> app/Services/ == app/Services/
            if remainder == impl_dir:
                logger.info(
                    "Found test %s for %s (prefix %s, full path match)",
                    fp,
                    impl_file_path,
                    tdp,
                )
                matches.append(fp)
                prefix_matched = True
                break

            # e.g. tests/php/unit/Services/ -> Services/ matches suffix of app/Services/
            for i in range(len(impl_parts) + 1):
                if "/".join(impl_parts[i:]) == remainder:
                    logger.info(
                        "Found test %s for %s (prefix %s, suffix match)",
                        fp,
                        impl_file_path,
                        tdp,
                    )
                    matches.append(fp)
                    prefix_matched = True
                    # Found a matching suffix, no need to try shorter ones
                    break

            if prefix_matched:
                # Found a match, no need to try other prefixes
                break

        if prefix_matched:
            # Custom prefix already found the test, no need for mirror matching
            continue

        # Mirror directory: find test dir component(s) in test path, strip them, then check if the remaining structural subpath matches impl subpath.
        # Handles leading (test/services/), mid-path (core/tests/Unit/Service/), and deep (core/tests/Feature/Api/V1/) test dirs.
        matched = False
        for start, part in enumerate(test_parts):
            if part not in TEST_DIR_NAMES:
                continue
            end = start + 1
            while end < len(test_parts) and test_parts[end] in TEST_DIR_NAMES:
                end += 1
            prefix = test_parts[:start]
            suffix = test_parts[end:]

            # Strategy 1: prefix + suffix as suffix of impl_dir (strict)
            mirror_subpath = "/".join(prefix + suffix)
            for i in range(len(impl_parts) + 1):
                if "/".join(impl_parts[i:]) == mirror_subpath:
                    matched = True
                    break
            if matched:
                break

            # Strategy 2: prefix is shared but mid-path diverges
            # e.g. core/tests/Feature/Api/V1/ for core/app/Http/Controllers/Api/V1/ prefix "core" matches, but "app/Http/Controllers" differs from "tests/Feature"
            prefix_path = "/".join(prefix)
            # Different repo root, this test dir can't mirror this impl
            if prefix_path and not impl_dir.startswith(prefix_path):
                continue

            suffix_path = "/".join(suffix)
            for i in range(len(impl_parts) + 1):
                impl_suffix = "/".join(impl_parts[i:])
                if impl_suffix == suffix_path:
                    matched = True
                    # Exact suffix match
                    break

                # Plural tolerance: "Service" matches "Services" (Laravel convention)
                if (
                    len(impl_suffix) == len(suffix_path) + 1
                    and impl_suffix == suffix_path + "s"
                ):
                    matched = True
                    break

                if (
                    len(suffix_path) == len(impl_suffix) + 1
                    and suffix_path == impl_suffix + "s"
                ):
                    matched = True
                    break

            if matched:
                # Found mirror match, no need to try other test dir components
                break

        if matched:
            logger.info("Found test %s for %s (mirror dir)", fp, impl_file_path)
            matches.append(fp)
        else:
            logger.info(
                "Skipping %s: same name as %s but unrelated directory",
                fp,
                impl_file_path,
            )

    logger.info("Found %d test files for %s", len(matches), impl_file_path)
    return matches
