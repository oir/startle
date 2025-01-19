# CLI from classes

Sometimes it is preferable to collect all of a program's configuration
in a class, possibly a dataclass, and pass that object around.
The `parse()` function supports such use cases as an alternative to the
[functional interface](/function-interface).
Given such a config class, `parse()` parses command-line arguments into it to construct
and return a config instance.

> [!INFO]
This usage builds directly on top of the functional interface
through the `__init__()` method of the class. Therefore this section assumes
familiarity with the [CLI from functions](/function-interface) to avoid
repetition.

## Example


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

Note how `parse()` is invoked with the `Config` _class_ as its argument, and
then returns a config object. Thus, `cfg` will be of type `Config`.

Then `dice.py` could be executed like:

<div id="dice-run-cast"></div>

The steps that are being performed under the hood is very similar to the functional interface:
`parse()`
- constructs an argument parser (based on `Config.__init__()`'s argument type hints, and defaults
  [which, in this case, comes automatically from the class attributes since it has the `dataclass`
   decorator]),
- parses the command-line arguments, i.e. process raw command-line strings and construct objects
  based on the provided type hints,
- provides the parsed objects as arguments to `Config`'s initializer, and constructs an object
  and returns it.

However, there are some differences too:
- Because `Config.__init__()` is implicit, argument descriptions are parsed from the class docstring
  from the section underneath `Attributes`.
- Similarly, since initializer is implicit, there is no `/` or `*` delimiters, which makes every
  argument positional as well as option.
- Since class docstring documents the config class, and not necessarily the program, it would be somewhat
  awkward to extract the _brief_ from the class docstring. Thus, anything other than the attribute
  descriptions are ignored. Instead, `parse()` takes in a `brief` argument explicitly to define the
  brief displayed when `--help` is passed:

<div id="dice-help-cast"></div>

Besides these points, argument specification is the same as
[argument specification in the function interface](/function-interface#argument-specification).


<script>
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
AsciinemaPlayer.create('cast/dice-help.cast', document.getElementById('dice-help-cast'), {
    autoPlay: true,
    controls: true,
    speed: 2,
    rows: 15,
    terminalFontFamily: "'Fira Mono', monospace",
    terminalFontSize: "12px",
    fit: false,
    theme: "custom-auto",
});
</script>