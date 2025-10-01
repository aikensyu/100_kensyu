"""
Overview:
    - Unit tests covering PromptBuilder search prompt generation to verify company names are injected.
Usage:
    - Execute `python -m unittest src.test_prompt_builder` from the repository root.
"""

import unittest

from prompt_builder import PromptBuilder


class PromptBuilderSearchPromptTests(unittest.TestCase):
    """Ensure company fields flow into rendered search prompts."""

    def setUp(self) -> None:
        self.builder = PromptBuilder(
            search_template="Find info about {{company_name}}",
            message_template="",
            self_info="",
        )
        self.company = {
            "company_name": "Acme Holdings",
            "company_name_encoded": "Acme+Holdings",
            "company_url": "https://acme.example",
        }

    def test_injects_company_name_placeholder(self) -> None:
        """`{{company_name}}` placeholder should be replaced with the raw name."""
        prompt = self.builder.render_search_prompt(self.company)
        self.assertEqual("Find info about Acme Holdings", prompt)

    def test_uses_encoded_name_when_requested(self) -> None:
        """`{{company_name_encoded}}` placeholder should use the encoded value."""
        builder = PromptBuilder(
            search_template="https://search.example?q={{company_name_encoded}}",
            message_template="",
            self_info="",
        )
        prompt = builder.render_search_prompt(self.company)
        self.assertEqual("https://search.example?q=Acme+Holdings", prompt)

    def test_fallbacks_to_url_when_template_blank(self) -> None:
        """Empty search template should fall back to the company URL."""
        builder = PromptBuilder(
            search_template="  ",
            message_template="",
            self_info="",
        )
        prompt = builder.render_search_prompt(self.company)
        self.assertEqual("https://acme.example", prompt)


if __name__ == "__main__":
    unittest.main()
