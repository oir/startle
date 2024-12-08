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
| `search_gh.py` | How to use `**kwargs`-style arguments to parse arbirary key-value pairs. |