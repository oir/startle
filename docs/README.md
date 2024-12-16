# startle

![tests](https://github.com/oir/startle/actions/workflows/test.yml/badge.svg)
[![Coverage Status](https://img.shields.io/coverallsCoverage/github/oir/startle?logo=Coveralls)](https://coveralls.io/github/oir/startle?branch=main)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/startle?logo=Python&logoColor=FFFFFF)](https://pypi.org/project/startle/)
[![PyPI Version](https://img.shields.io/pypi/v/startle?label=pip%20install%20startle&color=blue)](https://pypi.org/project/startle/)

!> **startle** is _alpha_ and should be considered unstable as its interface is fluid 😅, consider pinning to a version.

<div style="visibility: hidden; height: 0">

## Showcase

</div>

**startle** lets you transform a python function into a command line entry point, e.g:

`wc.py`:
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

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/help-dark.svg" width="100%">
  <source media="(prefers-color-scheme: light)" srcset="img/help-light.svg" width="100%">
  <img src="img/help-light.svg" width="100%">
</picture>

When you invoke `start`, it will construct an argparser (based on type hints and docstring),
parse the arguments, and invoke `word_count`.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/out-dark.svg" width="100%">
  <source media="(prefers-color-scheme: light)" srcset="img/out-light.svg" width="100%">
  <img src="img/out-light.svg" width="100%">
</picture>

## Highlights

**startle** is inspired by [Typer](https://github.com/fastapi/typer), and [Fire](https://github.com/google/python-fire),
but aims to be _non-intrusive_, to have stronger type support, and to have saner defaults.
Thus, some decisions are done differently:

- Use of positional-only or keyword-only argument separators (`/`, `*`, see PEP 570, 3102) are naturally translated into positional arguments or options.
  See above example ([wc.py](https://github.com/oir/startle/blob/main/examples/wc.py)).
- Like Typer and unlike Fire, type hints strictly determine how the individual arguments are parsed and typed.
- Short forms (e.g. `-k`, `-v` above) are automatically provided based on the initial of the argument.
- Variable length arguments are more intuitively handled.
  You can use `--things a b c` (in addition to `--things=a --things=b --things=c`).
  See [example](https://github.com/oir/startle/blob/main/examples/cat.py).
- Like Typer and unlike Fire, help is simply printed and not displayed in pager mode by default, so you can keep referring to it as you type your command.
- Like Fire and unlike Typer, docstrings determine the description of each argument in the help text, instead of having to individually add extra type annotations. This allows for a very non-intrusive design, you can adopt (or un-adopt) **startle** with no changes to your functions.
- `*args` but also `**kwargs` are supported, to parse unknown arguments as well as unknown options (`--unk-key unk-val`).
  See [example](https://github.com/oir/startle/blob/main/examples/search_gh.py).

See all [examples](https://github.com/oir/startle/tree/main/examples).
