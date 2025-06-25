import unittest

from utils.prompts.push_trigger import PUSH_TRIGGER_SYSTEM_PROMPT


class TestPushTriggerPrompt(unittest.TestCase):
    def test_prompt_includes_unit_tests(self):
        # Check that the prompt includes the phrase 'unit tests'
        self.assertIn('unit tests', PUSH_TRIGGER_SYSTEM_PROMPT)

    def test_prompt_ends_with_unit_testing_only(self):
        # Ensure the prompt ends with the specific phrase
        self.assertIn('actual changes made and unit testing only', PUSH_TRIGGER_SYSTEM_PROMPT)

    def test_prompt_instructions(self):
        # Check that all key instructions are present
        expected_instructions = [
            "Analyze commits and add missing unit tests based on the actual code changes.",
            "Identify code files that need unit test coverage based on the specific changes made",
            "Generate appropriate unit test cases that cover ONLY the changed functionality",
            "Commit the unit test files to the repository"
        ]
        for instruction in expected_instructions:
            with self.subTest(instruction=instruction):
                self.assertIn(instruction, PUSH_TRIGGER_SYSTEM_PROMPT)
    def test_prompt_structure(self):
        self.assertIn('Steps:', PUSH_TRIGGER_SYSTEM_PROMPT)
        self.assertIn('CRITICAL RULES:', PUSH_TRIGGER_SYSTEM_PROMPT)



if __name__ == '__main__':
    unittest.main()
