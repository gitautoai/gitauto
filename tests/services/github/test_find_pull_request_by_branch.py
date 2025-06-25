import unittest

from services.github.pull_requests.find_pull_request_by_branch import find_pull_request_by_branch


class TestFindPullRequestByBranch(unittest.TestCase):
    def test_removed_htmlUrl(self):
        # Call the function with a sample branch name
        # Adjust parameters as per actual function signature if needed
        query = find_pull_request_by_branch("feature-branch")
        
        # Ensure the query does not contain 'htmlUrl'
        self.assertNotIn("htmlUrl", query, "Query should not contain htmlUrl field after fix.")

        # Additionally, check that other expected fields are present
        self.assertIn("number", query, "Query should contain number field.")
        self.assertIn("title", query, "Query should contain title field.")
        self.assertIn("url", query, "Query should contain url field.")
        self.assertIn("headRef", query, "Query should contain headRef field.")
        self.assertIn("baseRef", query, "Query should contain baseRef field.")


if __name__ == "__main__":
    unittest.main()
