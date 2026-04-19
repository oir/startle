from typing import TypedDict

from typing_extensions import NotRequired, Required

from ._utils import NS, OS, TS, VS, check_help_from_class


def dopt(s: str) -> str:
    return f"[{OS} dim]{s}[/]"


def name(s: str) -> str:
    return f"[{NS} {OS}]{s}[/]"


def dname(s: str) -> str:
    return f"[{NS} {OS} dim]{s}[/]"


def var(s: str) -> str:
    return f"[{VS}]{s}[/]"


def test_typeddict_not_required_optional_marker():
    class Cfg(TypedDict):
        """
        A config.

        Attributes:
            name: The name.
            age: The age.
        """

        name: NotRequired[str]
        age: NotRequired[int]

    expected = f"""\

A config.

[{TS}]Usage:[/]
  cfg.py [{name("--name")} {var("<text>")}] [{name("--age")} {var("<int>")}]

[{TS}]where[/]
  [dim](option)[/]  {name("-n")}{dopt("|")}{name("--name")} {var("<text>")}  [i]The name.[/] [{OS}](optional)[/]
  [dim](option)[/]  {name("-a")}{dopt("|")}{name("--age")} {var("<int>")}    [i]The age.[/] [{OS}](optional)[/]
  [dim](option)[/]  {dname("-?")}{dopt("|")}{dname("--help")}         [i dim]Show this help message and exit.[/]
"""

    check_help_from_class(Cfg, "A config.", "cfg.py", expected)


def test_typeddict_total_false_mixed_with_required():
    class Cfg(TypedDict, total=False):
        """
        A config.

        Attributes:
            name: The name.
            age: The age.
            label: The label.
        """

        name: str
        age: Required[int]
        label: NotRequired[str]

    expected = f"""\

A config.

[{TS}]Usage:[/]
  cfg.py [{name("--name")} {var("<text>")}] {name("--age")} {var("<int>")} [{name("--label")} {var("<text>")}]

[{TS}]where[/]
  [dim](option)[/]  {name("-n")}{dopt("|")}{name("--name")} {var("<text>")}   [i]The name.[/] [{OS}](optional)[/]
  [dim](option)[/]  {name("-a")}{dopt("|")}{name("--age")} {var("<int>")}     [i]The age.[/] [yellow](required)[/]
  [dim](option)[/]  {name("-l")}{dopt("|")}{name("--label")} {var("<text>")}  [i]The label.[/] [{OS}](optional)[/]
  [dim](option)[/]  {dname("-?")}{dopt("|")}{dname("--help")}          [i dim]Show this help message and exit.[/]
"""

    check_help_from_class(Cfg, "A config.", "cfg.py", expected)
