"""
Example invocations (for fish shell):
 ❯ python examples/cat.py examples/wc.py examples/cat.py --delim=\n===\n\n
 ❯ python examples/cat.py --delim=\n===\n\n examples/cat.py examples/wc.py
"""

from pathlib import Path

from startle import start


def cat(files: list[Path], /, *, delim: str = "") -> None:
    """
    Concatenate files with an optional delimiter.

    Args:
        files: The files to concatenate.
        delim: The delimiter to use.
    """

    for i, file in enumerate(files):
        if i:
            print(delim, end="")
        print(file.read_text(), end="")


start(cat)
