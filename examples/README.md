# Examples

This folder contains standalone example scripts for how to do
various things with **startle**.
Each file can be invoked as a command line entry point, thus
you can inspect with `python <example> --help`.

| example | what it illustrates |
| -- | -- |
| `wc.py` | "Word count." Most basic example showing the library use. |
| `cat.py` | Shows an example with a list argument (similar to `nargs` from `argparse`). |
| `color.py` | Using enums or Literals to represent "choices". |
| `calc.py` | How to use multiple (free) functions as commands, instead of invoking a single function. |
| `rational.py` | How to register a perser for a custom user type to make it parsable. |
| `ls.py` | How to use `*args`-style arguments to parse arbitrary (unknown) positional arguments. |
| `search_gh.py` | How to use `**kwargs`-style arguments to parse arbirary key-value pairs. |
| `dice.py` | How to use `parse()` to parse args into a class. |
| `dice2.py` | How to use `parse()` to parse args into a dict using a `TypedDict` definition. |
| `digits.py` | A recursive parsing example composing dataclasses and a main function signature. |