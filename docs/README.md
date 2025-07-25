<div align="center">
<div style="margin-bottom: -20px">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/logo-dark.png" width="400">
  <source media="(prefers-color-scheme: light)" srcset="img/logo-light.png" width="400">
  <img src="img/logo-light.png" width="400">
</picture>
</div>

_Give your code a start._ ⚡👀

![tests](https://github.com/oir/startle/actions/workflows/test.yml/badge.svg)
[![codecov](https://codecov.io/gh/oir/startle/graph/badge.svg?token=2MCJPOJWFA)](https://codecov.io/gh/oir/startle)
[![Docs](https://img.shields.io/badge/docs-2ECE53?logo=docsify&logoColor=fff)](https://oir.github.io/startle/)
<br>
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/startle?logo=Python&logoColor=FFFFFF)](https://pypi.org/project/startle/)
[![PyPI Version](https://img.shields.io/pypi/v/startle?label=pip%20install%20startle&color=blue&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA1MTIgNTEyIj48IS0tIUZvbnQgQXdlc29tZSBGcmVlIDYuNy4yIGJ5IEBmb250YXdlc29tZSAtIGh0dHBzOi8vZm9udGF3ZXNvbWUuY29tIExpY2Vuc2UgLSBodHRwczovL2ZvbnRhd2Vzb21lLmNvbS9saWNlbnNlL2ZyZWUgQ29weXJpZ2h0IDIwMjQgRm9udGljb25zLCBJbmMuLS0+PHBhdGggZmlsbD0iI2VhZWJlZSIgZD0iTTI4OCAzMmMwLTE3LjctMTQuMy0zMi0zMi0zMnMtMzIgMTQuMy0zMiAzMmwwIDI0Mi43LTczLjQtNzMuNGMtMTIuNS0xMi41LTMyLjgtMTIuNS00NS4zIDBzLTEyLjUgMzIuOCAwIDQ1LjNsMTI4IDEyOGMxMi41IDEyLjUgMzIuOCAxMi41IDQ1LjMgMGwxMjgtMTI4YzEyLjUtMTIuNSAxMi41LTMyLjggMC00NS4zcy0zMi44LTEyLjUtNDUuMyAwTDI4OCAyNzQuNyAyODggMzJ6TTY0IDM1MmMtMzUuMyAwLTY0IDI4LjctNjQgNjRsMCAzMmMwIDM1LjMgMjguNyA2NCA2NCA2NGwzODQgMGMzNS4zIDAgNjQtMjguNyA2NC02NGwwLTMyYzAtMzUuMy0yOC43LTY0LTY0LTY0bC0xMDEuNSAwLTQ1LjMgNDUuM2MtMjUgMjUtNjUuNSAyNS05MC41IDBMMTY1LjUgMzUyIDY0IDM1MnptMzY4IDU2YTI0IDI0IDAgMSAxIDAgNDggMjQgMjQgMCAxIDEgMC00OHoiLz48L3N2Zz4=)](https://pypi.org/project/startle/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/types-mypy-blue.svg)](https://github.com/python/mypy)

</div>

> [!ATTENTION]
**Startle** is _alpha_ and should be considered unstable as its interface is fluid 😅.
Consider pinning to a version.

**Status:** A useable MVP for parsing into functions and classes. Unstable interface. <br>
**Roadmap:** See [project board](https://github.com/users/oir/projects/3).

---

<div style="visibility: hidden; height: 0">

## Showcase

</div>

**Startle** lets you transform a python function (or functions) into a command line entry point, e.g:

<div class="code-file" style="--filename:'wc.py'">


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

</div>

<div id="wc-help-cast"></div>

When you invoke `start()`, it will construct an argparser (based on type hints and docstring),
parse the arguments, and invoke `word_count`.

<div id="wc-run-cast"></div>

You can also invoke `start()` with a list of functions instead of a single function.
In this case, functions are made available as _commands_ with their own arguments
and options in your CLI. See [here](/function-interface#commands).

---

**Startle** also allows you to transform a class (possibly a dataclass) into a command line parser:

<div class="code-file" style="--filename:'dice.py'">

```python
import random
from dataclasses import dataclass
from typing import Literal

from startle import parse


@dataclass
class Config:
    """
    Configuration for the dice program.

    Attributes:
        sides: The number of sides on the dice.
        count: The number of dice to throw.
        kind: Whether to throw a single die or a pair of dice.
    """

    sides: int = 6
    count: int = 1
    kind: Literal["single", "pair"] = "single"


def throw_dice(cfg: Config) -> None:
    """
    Throw the dice according to the configuration.
    """
    if cfg.kind == "single":
        for _ in range(cfg.count):
            print(random.randint(1, cfg.sides))
    else:
        for _ in range(cfg.count):
            print(random.randint(1, cfg.sides), random.randint(1, cfg.sides))


if __name__ == "__main__":
    cfg = parse(Config, brief="A program to throw dice.")
    throw_dice(cfg)
```

</div>

Then `dice.py` could be executed like:

<div id="dice-run-cast"></div>


## Motivation

**Startle** is inspired by [Typer](https://github.com/fastapi/typer), [Fire](https://github.com/google/python-fire),
and [HFArgumentParser](https://github.com/huggingface/transformers/blob/main/src/transformers/hf_argparser.py),
but aims to be _non-intrusive_, to have stronger type support, and to have saner defaults.
Thus, some decisions are done differently:

- Use of positional-only or keyword-only argument separators (`/`, `*`, see PEP [570](https://peps.python.org/pep-0570/),
  [3102](https://peps.python.org/pep-3102/)) are naturally translated into positional arguments or options.
  See above example ([wc.py](https://github.com/oir/startle/blob/main/examples/wc.py)).
- Like Typer and unlike Fire, type hints strictly determine how the individual arguments are parsed and typed.
- Short forms (e.g. `-k`, `-v` above) are automatically provided based on the initial of the argument.
- Variable length arguments are more intuitively handled.
  You can use `--things a b c` (in addition to `--things=a --things=b --things=c`).
  See [example](https://github.com/oir/startle/blob/main/examples/cat.py).
- Like Typer and unlike Fire, help is simply printed and not displayed in pager mode by default, so you can keep referring to it as you type your command.
- Like Fire and unlike Typer, docstrings determine the description of each argument in the help text, instead of having to individually add extra type annotations. This allows for a very non-intrusive design, you can adopt (or un-adopt) **Startle** with no changes to your functions.
- `*args` but also `**kwargs` are supported, to parse unknown arguments as well as unknown options (`--unk-key unk-val`).
  See [example](https://github.com/oir/startle/blob/main/examples/search_gh.py).

See all [examples](https://github.com/oir/startle/tree/main/examples).


<script>
AsciinemaPlayer.create('cast/wc-help.cast', document.getElementById('wc-help-cast'), {
    autoPlay: true,
    controls: true,
    rows: 14,
    terminalFontFamily: "'Fira Mono', monospace",
    terminalFontSize: "12px",
    fit: false,
    theme: "custom-auto",
});
AsciinemaPlayer.create('cast/wc-run.cast', document.getElementById('wc-run-cast'), {
    autoPlay: true,
    controls: true,
    rows: 3,
    terminalFontFamily: "'Fira Mono', monospace",
    terminalFontSize: "12px",
    fit: false,
    theme: "custom-auto",
});
AsciinemaPlayer.create('cast/dice-run.cast', document.getElementById('dice-run-cast'), {
    autoPlay: true,
    controls: true,
    speed: 2,
    rows: 7,
    terminalFontFamily: "'Fira Mono', monospace",
    terminalFontSize: "12px",
    fit: false,
    theme: "custom-auto",
});
</script>


