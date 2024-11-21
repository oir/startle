# startle

![tests](https://github.com/oir/startle/actions/workflows/test.yml/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/oir/startle/badge.svg?branch=main)](https://coveralls.io/github/oir/startle?branch=main)

> [!WARNING]  
> **startle** is _alpha_ and should be considered unstable as its interface is fluid 😅, consider pinning to a version.

**startle** lets you transform a python function into a command line entry point:
```python
from pathlib import Path
from typing import Literal

from startle import start


def word_count(
    fname: Path, /, kind: Literal["word", "char"] = "word", *, verbose: bool = False
) -> None:
    """
    Count the number of words or characters in a file.

    Args:
        fname: The file to count.
        kind: Whether to count words or characters.
        verbose: Whether to print additional info.
    """

    text = open(fname).read()
    count = len(text.split()) if kind == "word" else len(text)

    print(f"{count} {kind}s in {fname}" if verbose else count)


start(word_count)
```