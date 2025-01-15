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

`dice.py`:

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

Note how `parse()` is invoked with the `Config` _class_ as its argument, and
then returns a config object. Thus, `cfg` will be of type `Config`.

Then `dice.py` could be executed like:

```bash
~ ❯ python examples/dice.py --sides 6 --count 5 --kind pair
3 1
4 4
1 4
3 1
2 1
~ ❯
```

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

  ```bash
  ~ ❯ python examples/dice.py --help

  A program to throw dice.

  Usage:
  examples/dice.py [--sides <int>] [--count <int>] [--kind single|pair]

  where
  (pos. or opt.)  -s|--sides <int>       The number of sides on the dice. (default: 6)
  (pos. or opt.)  -c|--count <int>       The number of dice to throw. (default: 1)
  (pos. or opt.)  -k|--kind single|pair  Whether to throw a single die or a pair of dice. (default: single)
  (option)        -?|--help              Show this help message and exit.

  ~ ❯
  ```

Besides these points, argument specification is the same as
[argument specification in the function interface](/function-interface#argument-specification).