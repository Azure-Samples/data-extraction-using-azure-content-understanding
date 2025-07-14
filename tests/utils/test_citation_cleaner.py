import unittest
from src.utils.citation_cleaner import (
    remove_inline_citations_preserve_spacing
)


class TestCitationCleaner(unittest.TestCase):
    """Test cases for the citation_cleaner utility functions."""

    def test_remove_inline_citations_basic(self):
        """Test basic citation removal."""
        text = "This is a text [1] with multiple [2] citations [3]."
        expected = "This is a text with multiple citations."
        self.assertEqual(remove_inline_citations_preserve_spacing(text), expected)

    def test_remove_inline_citations_empty(self):
        """Test with empty strings."""
        self.assertEqual(remove_inline_citations_preserve_spacing(""), "")
        self.assertEqual(remove_inline_citations_preserve_spacing(None), None)

    def test_remove_inline_citations_no_citations(self):
        """Test with text that has no citations."""
        text = "This text has no citations."
        self.assertEqual(remove_inline_citations_preserve_spacing(text), text)

    def test_remove_inline_citations_adjacent(self):
        """Test with adjacent citations."""
        text = "Adjacent citations[1][2][3] should be removed."
        expected = "Adjacent citations should be removed."
        self.assertEqual(remove_inline_citations_preserve_spacing(text), expected)

    def test_remove_inline_citations_large_numbers(self):
        """Test with large citation numbers."""
        text = "Citation [123] with large [9999] numbers."
        expected = "Citation with large numbers."
        self.assertEqual(remove_inline_citations_preserve_spacing(text), expected)

    def test_preserve_spacing_between_words(self):
        """Test spacing preservation between words."""
        text = "Word[1]adjacent and word [2] with space."
        expected = "Word adjacent and word with space."
        self.assertEqual(remove_inline_citations_preserve_spacing(text), expected)
