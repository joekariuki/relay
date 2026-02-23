"""Response text formatting and cleaning utilities.

Cleans Claude's raw response text by removing emojis and normalizing whitespace
for a professional customer support experience.
"""

from __future__ import annotations

import re

# Compiled regex for emoji removal — covers common Unicode emoji ranges
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map
    "\U0001f1e0-\U0001f1ff"  # flags (regional indicators)
    "\U00002702-\U000027b0"  # dingbats
    "\U000024c2-\U0001f251"  # enclosed characters
    "\U0001f900-\U0001f9ff"  # supplemental symbols
    "\U0001fa00-\U0001fa6f"  # chess symbols
    "\U0001fa70-\U0001faff"  # symbols extended-A
    "\U00002600-\U000026ff"  # misc symbols
    "\U0000fe00-\U0000fe0f"  # variation selectors
    "\U0000200d"             # zero-width joiner
    "]+",
    re.UNICODE,
)

# Collapse 3+ consecutive newlines into 2
_EXCESSIVE_NEWLINES = re.compile(r"\n{3,}")


def clean_response_text(text: str) -> str:
    """Clean and normalize response text from Claude.

    Applies in order:
    1. Strip emoji characters
    2. Collapse 3+ consecutive newlines to 2 (preserving paragraph breaks)
    3. Strip trailing whitespace from each line
    4. Strip leading/trailing whitespace from the full text
    """
    text = _EMOJI_PATTERN.sub("", text)
    text = _EXCESSIVE_NEWLINES.sub("\n\n", text)
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()
