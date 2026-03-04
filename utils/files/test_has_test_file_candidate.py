from utils.files.has_test_file_candidate import has_test_file_candidate


def test_colocated_test_file():
    all_files = ["src/utils/generateId.ts", "src/utils/generateId.test.ts"]
    assert has_test_file_candidate("src/utils/generateId.ts", all_files) is True


def test_tests_subdirectory():
    all_files = [
        "src/models/Quote.ts",
        "src/models/__tests__/Quote.test.ts",
    ]
    assert has_test_file_candidate("src/models/Quote.ts", all_files) is True


def test_same_name_different_directory_no_match():
    # src/utils/generateId.test.ts should NOT match src/models/.../generateId.ts
    all_files = [
        "src/models/graphql/operation/document/generateId.ts",
        "src/utils/generateId.test.ts",
    ]
    assert (
        has_test_file_candidate(
            "src/models/graphql/operation/document/generateId.ts", all_files
        )
        is False
    )


def test_no_test_file_at_all():
    all_files = ["src/utils/generateId.ts", "src/utils/helpers.ts"]
    assert has_test_file_candidate("src/utils/generateId.ts", all_files) is False


def test_tests_subdirectory_plural():
    all_files = [
        "src/models/Quote.ts",
        "src/models/tests/Quote.test.ts",
    ]
    assert has_test_file_candidate("src/models/Quote.ts", all_files) is True


def test_test_subdirectory_singular():
    all_files = [
        "src/models/Quote.ts",
        "src/models/test/Quote.test.ts",
    ]
    assert has_test_file_candidate("src/models/Quote.ts", all_files) is True


def test_spec_subdirectory():
    all_files = [
        "src/models/Quote.ts",
        "src/models/spec/Quote.spec.ts",
    ]
    assert has_test_file_candidate("src/models/Quote.ts", all_files) is True


def test_e2e_subdirectory():
    all_files = [
        "src/models/Quote.ts",
        "src/models/e2e/Quote.test.ts",
    ]
    assert has_test_file_candidate("src/models/Quote.ts", all_files) is True


def test_test_file_in_distant_tests_directory():
    # test/ mirror directory at root should NOT match
    all_files = [
        "src/utils/generateId.ts",
        "test/utils/generateId.test.ts",
    ]
    assert has_test_file_candidate("src/utils/generateId.ts", all_files) is False


def test_case_insensitive_stem_match():
    all_files = ["src/utils/GenerateId.ts", "src/utils/generateid.test.ts"]
    assert has_test_file_candidate("src/utils/GenerateId.ts", all_files) is True


def test_partial_stem_match_in_same_dir():
    # "generate" is in "generateId.test.ts" stem
    all_files = ["src/utils/generate.ts", "src/utils/generateId.test.ts"]
    assert has_test_file_candidate("src/utils/generate.ts", all_files) is True


def test_non_test_file_with_matching_name():
    all_files = ["src/utils/generateId.ts", "src/utils/generateId.utils.ts"]
    assert has_test_file_candidate("src/utils/generateId.ts", all_files) is False
