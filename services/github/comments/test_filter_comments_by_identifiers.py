import pytest
from unittest.mock import patch

from services.github.comments.filter_comments_by_identifiers import filter_comments_by_identifiers


def test_filter_comments_by_identifiers_empty_comments():
    """Test with empty comments list"""
    result = filter_comments_by_identifiers([], ["identifier"])
    assert result == []


def test_filter_comments_by_identifiers_none_comments():
    """Test with None comments list"""
    result = filter_comments_by_identifiers(None, ["identifier"])
    assert result == []


def test_filter_comments_by_identifiers_empty_identifiers():
    """Test with empty identifiers list"""
    comments = [
        {
            "id": 1,
            "body": "Test comment",
            "user": {"login": "gitauto-ai[bot]"}
        }
    ]
    
    with patch("services.github.comments.filter_comments_by_identifiers.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):
        result = filter_comments_by_identifiers(comments, [])
        assert result == []


def test_filter_comments_by_identifiers_matching_comment():
    """Test with matching comment containing identifier and correct user"""
    comments = [
        {
            "id": 1,
            "body": "This comment contains the test-identifier",
            "user": {"login": "gitauto-ai[bot]"}
        }
    ]
    
    with patch("services.github.comments.filter_comments_by_identifiers.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):
        result = filter_comments_by_identifiers(comments, ["test-identifier"])
        assert len(result) == 1
        assert result[0]["id"] == 1


def test_filter_comments_by_identifiers_wrong_user():
    """Test with comment containing identifier but from wrong user"""
    comments = [
        {
            "id": 1,
            "body": "This comment contains the test-identifier",
            "user": {"login": "other-user"}
        }
    ]
    
    with patch("services.github.comments.filter_comments_by_identifiers.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):
        result = filter_comments_by_identifiers(comments, ["test-identifier"])
        assert result == []


def test_filter_comments_by_identifiers_no_identifier_match():
    """Test with comment from correct user but no identifier match"""
    comments = [
        {
            "id": 1,
            "body": "This comment does not contain the target",
            "user": {"login": "gitauto-ai[bot]"}
        }
    ]
    
    with patch("services.github.comments.filter_comments_by_identifiers.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):
        result = filter_comments_by_identifiers(comments, ["test-identifier"])
        assert result == []


def test_filter_comments_by_identifiers_multiple_identifiers():
    """Test with multiple identifiers, some matching"""
    comments = [
        {
            "id": 1,
            "body": "This comment contains first-identifier",
            "user": {"login": "gitauto-ai[bot]"}
        },
        {
            "id": 2,
            "body": "This comment contains second-identifier",
            "user": {"login": "gitauto-ai[bot]"}
        },
        {
            "id": 3,
            "body": "This comment contains no match",
            "user": {"login": "gitauto-ai[bot]"}
        }
    ]
    
    with patch("services.github.comments.filter_comments_by_identifiers.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):
        result = filter_comments_by_identifiers(comments, ["first-identifier", "second-identifier"])
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2


def test_filter_comments_by_identifiers_mixed_users():
    """Test with mixed users, only GitAuto comments should be returned"""
    comments = [
        {
            "id": 1,
            "body": "GitAuto comment with test-identifier",
            "user": {"login": "gitauto-ai[bot]"}
        },
        {
            "id": 2,
            "body": "User comment with test-identifier",
            "user": {"login": "regular-user"}
        },
        {
            "id": 3,
            "body": "Another GitAuto comment with test-identifier",
            "user": {"login": "gitauto-ai[bot]"}
        }
    ]
    
    with patch("services.github.comments.filter_comments_by_identifiers.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):
        result = filter_comments_by_identifiers(comments, ["test-identifier"])
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 3


def test_filter_comments_by_identifiers_partial_match():
    """Test that partial matches work correctly"""
    comments = [
        {
            "id": 1,
            "body": "This is a test-identifier-suffix comment",
            "user": {"login": "gitauto-ai[bot]"}
        },
        {
            "id": 2,
            "body": "This is a prefix-test-identifier comment",
            "user": {"login": "gitauto-ai[bot]"}
        }
    ]
    
    with patch("services.github.comments.filter_comments_by_identifiers.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):
        result = filter_comments_by_identifiers(comments, ["test-identifier"])
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2


def test_filter_comments_by_identifiers_exception_handling():
    """Test that the function handles exceptions gracefully due to @handle_exceptions decorator"""
    # Test with malformed comment structure
    malformed_comments = [
        {
            "id": 1,
            "body": "test-identifier",
            # Missing "user" key
        }
    ]
    
    with patch("services.github.comments.filter_comments_by_identifiers.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):
        result = filter_comments_by_identifiers(malformed_comments, ["test-identifier"])
        # Should return empty list due to @handle_exceptions decorator with default_return_value=[]
        assert result == []


def test_filter_comments_by_identifiers_case_sensitive():
    """Test that identifier matching is case sensitive"""
    comments = [
        {
            "id": 1,
            "body": "This comment contains TEST-IDENTIFIER",
            "user": {"login": "gitauto-ai[bot]"}
        }
    ]
    
    with patch("services.github.comments.filter_comments_by_identifiers.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):
        result = filter_comments_by_identifiers(comments, ["test-identifier"])
        assert result == []
        
        result = filter_comments_by_identifiers(comments, ["TEST-IDENTIFIER"])
        assert len(result) == 1
        assert result[0]["id"] == 1


def test_filter_comments_by_identifiers_multiple_identifiers_single_comment():
    """Test with single comment matching multiple identifiers"""
    comments = [
        {
            "id": 1,
            "body": "This comment contains both first-id and second-id identifiers",
            "user": {"login": "gitauto-ai[bot]"}
        }
    ]
    
    with patch("services.github.comments.filter_comments_by_identifiers.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"):
        result = filter_comments_by_identifiers(comments, ["first-id", "second-id"])
        assert len(result) == 1
        assert result[0]["id"] == 1
