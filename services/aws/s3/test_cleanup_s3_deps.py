# pyright: reportUnusedVariable=false
from unittest.mock import patch

from services.aws.s3.cleanup_s3_deps import cleanup_s3_deps

MODULE = "services.aws.s3.cleanup_s3_deps"


def test_deletes_s3_objects():
    with patch(f"{MODULE}.s3_client") as mock_s3:
        mock_s3.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "owner/repo/node_modules.tar.gz"},
                {"Key": "owner/repo/manifests/package.json"},
            ]
        }

        result = cleanup_s3_deps("owner", "repo")

        assert mock_s3.delete_object.call_count == 2
        assert result is True


def test_returns_true_when_no_objects():
    with patch(f"{MODULE}.s3_client") as mock_s3:
        mock_s3.list_objects_v2.return_value = {"Contents": []}

        result = cleanup_s3_deps("owner", "repo")

        mock_s3.delete_object.assert_not_called()
        assert result is True
