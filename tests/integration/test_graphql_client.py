import unittest
from services.github.graphql_client import get_graphql_client
from tests.constants import TOKEN

# Integration test for GitHub GraphQL client
# See: https://docs.github.com/en/graphql

class TestGraphqlClient(unittest.TestCase):
    def test_get_graphql_client(self):
        # Create a GraphQL client for GitHub API using TOKEN from constants
        client = get_graphql_client(TOKEN)
        # GraphQL query to fetch GitHub rate limit information
        query = """
        query {
            rateLimit {
                cost
                remaining
                resetAt
            }
        }
        """
        try:
            result = client.execute(query)
        except Exception as e:
            self.fail(f"GraphQL query failed with error: {e}")
        self.assertIn("rateLimit", result)
        self.assertIsInstance(result["rateLimit"]["remaining"], int)

if __name__ == "__main__":
    unittest.main()
