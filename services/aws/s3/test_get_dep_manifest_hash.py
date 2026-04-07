from services.aws.s3.get_dep_manifest_hash import get_dep_manifest_hash


def test_hash_is_deterministic():
    hash1 = get_dep_manifest_hash(["content1", "content2"])
    hash2 = get_dep_manifest_hash(["content1", "content2"])
    assert hash1 == hash2


def test_hash_changes_with_different_content():
    hash1 = get_dep_manifest_hash(["content1", "content2"])
    hash2 = get_dep_manifest_hash(["content1", "content3"])
    assert hash1 != hash2


def test_none_values_are_skipped():
    hash1 = get_dep_manifest_hash(["content1", None, "content2"])
    hash2 = get_dep_manifest_hash(["content1", "content2"])
    assert hash1 == hash2


def test_empty_list_returns_sha256_of_empty():
    result = get_dep_manifest_hash([])
    # SHA256 of empty string
    assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_hash_is_64_char_hex():
    result = get_dep_manifest_hash(["test"])
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)
