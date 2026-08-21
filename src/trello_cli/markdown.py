"""Helpers for keeping Markdown text intact across LLM/CLI boundaries."""

import re


# Only decode newline escapes.  Decoding the whole string as JSON would also
# change ordinary backslashes in Markdown (for example ``\\*`` or a Windows
# path), which is surprising for a text field.
_ESCAPED_NEWLINE = re.compile(r"(?<!\\)\\r\\n|(?<!\\)\\n|(?<!\\)\\r")


def normalize_markdown(text: str) -> str:
    """Turn literal ``\\n``/``\\r\\n`` sequences into line breaks.

    Real line breaks are left untouched.  A doubled backslash is preserved so
    callers can still intentionally write a literal ``\\n``.
    """

    return _ESCAPED_NEWLINE.sub("\n", text)
