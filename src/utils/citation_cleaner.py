import re


def remove_inline_citations_preserve_spacing(text: str) -> str:
    """Removes all inline citations in the format [number] from a string, preserving proper spacing between words.

    Args:
        text (str): The text containing inline citations.

    Returns:
        str: The text with all inline citations removed and spacing fixed.

    Examples:
        >>> remove_inline_citations_preserve_spacing("This is a text[1] with multiple[2] citations[3].")
        'This is a text with multiple citations.'
    """
    if not text:
        return text

    # Replace citations with a space if they're between words without spaces
    result = re.sub(r'(\S)\[\d+\](\S)', r'\1 \2', text)

    # Then remove all remaining citations
    result = re.sub(r'\[\d+\]', '', result)

    # Fix any double spaces that might have been created
    result = re.sub(r'\s{2,}', ' ', result)

    # Fix spacing before punctuation
    result = re.sub(r'\s+([,.;:!?])', r'\1', result)

    return result
