from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Callable

from pytest import mark

from ._utils import NS, OS, TS, VS, check_help_from_class, check_help_from_func


def dopt(s: str) -> str:
    return f"[{OS} dim]{s}[/]"


def name(s: str) -> str:
    return f"[{NS} {OS}]{s}[/]"


def dname(s: str) -> str:
    return f"[{NS} {OS} dim]{s}[/]"


def pos(left: str, right: str) -> str:
    return f"[{VS}]<[{NS}]{left}:[/]{right}>[/]"


def dpos(left: str, right: str) -> str:
    return f"[{VS} dim]<[{NS}]{left}:[/]{right}>[/]"


def var(s: str) -> str:
    return f"[{VS}]{s}[/]"


def dvar(s: str) -> str:
    return f"[{VS} dim]{s}[/]"


def test_func_simple():
    def fusion(
        left_path: str,
        right_path: str,
        /,
        output_path: str = "",
        *,
        components: list[str] = ["fang", "claw"],
        alpha: float = 0.5,
    ):
        """
        Fuse two monsters with polymerization.

        Args:
            left_path: Path to the first monster.
            right_path: Path to the second monster.
            output_path: Path to store the fused monster.
            components: Components to fuse.
            alpha: Weighting factor for the first monster.
        """
        print(f"left_path: {left_path}")
        print(f"right_path: {right_path}")
        print(f"output_path: {output_path}")
        print(f"components: {components}")
        print(f"alpha: {alpha}")

    def fusion2(
        left_path: str,
        right_path: str,
        /,
        output_path: str = "",
        *,
        components: list[str] = ["fang", "claw"],
        alpha: float = 0.5,
    ):
        """
        Fuse two monsters with polymerization.

        Args:
            left_path (str): Path to the first monster.
            right_path (str): Path to the second monster.
            output_path (str): Path to store the fused monster.
            components (list[str]): Components to fuse.
            alpha (float): Weighting factor for the first monster.
        """
        print(f"left_path: {left_path}")
        print(f"right_path: {right_path}")
        print(f"output_path: {output_path}")
        print(f"components: {components}")
        print(f"alpha: {alpha}")

    expected = f"""\

Fuse two monsters with polymerization.

[{TS}]Usage:[/]
  fuse.py {pos("left-path", "text")} {pos("right-path", "text")} [{name("--output-path")} {var("<text>")}] [{name("--components")} {var("<text>")} [dim][[/]{dvar("<text>")}[dim] ...][/]] [{name("--alpha")} {var("<float>")}]

[{TS}]where[/]
  [dim](positional)[/]    {pos("left-path", "text")}                     [i]Path to the first monster.[/] [yellow](required)[/]                 
  [dim](positional)[/]    {pos("right-path", "text")}                    [i]Path to the second monster.[/] [yellow](required)[/]                
  [dim](pos. or opt.)[/]  {name("-o")}{dopt('|')}{name("--output-path")} {var("<text>")}              [i]Path to store the fused monster.[/] [green](default: [/][green dim]""[/][green])[/]        
  [dim](option)[/]        {name("-c")}{dopt('|')}{name("--components")} {var("<text>")} [dim][[/]{dvar("<text>")}[dim] ...][/]  [i]Components to fuse.[/] [green](default: [/][green]['fang', 'claw'][/][green])[/]       
  [dim](option)[/]        {name("-a")}{dopt('|')}{name("--alpha")} {var("<float>")}                   [i]Weighting factor for the first monster.[/] [green](default: [/][green]0.5[/][green])[/]
  [dim](option)[/]        {dname("-?")}{dopt('|')}{dname("--help")}                            [i dim]Show this help message and exit.[/]                      
"""

    check_help_from_func(fusion, "fuse.py", expected)
    check_help_from_func(fusion2, "fuse.py", expected)


def test_class_simple():
    class FusionConfig:
        """
        Fusion config.

        Attributes:
            left_path: Path to the first monster.
            right_path: Path to the second monster.
            output_path: Path to store the fused monster.
            components: Components to fuse.
            alpha: Weighting factor for the first monster.
        """

        def __init__(
            self,
            left_path: str,
            right_path: str,
            /,
            output_path: str,
            *,
            components: list[str] = ["fang", "claw"],
            alpha: float = 0.5,
        ):
            self.left_path = left_path
            self.right_path = right_path
            self.output_path = output_path
            self.components = components
            self.alpha = alpha

    expected = f"""\

Fuse two monsters with polymerization.

[{TS}]Usage:[/]
  fuse.py {pos("left-path", "text")} {pos("right-path", "text")} {name("--output-path")} {var("<text>")} [{name("--components")} {var("<text>")} [dim][[/]{dvar("<text>")}[dim] ...][/]] [{name("--alpha")} {var("<float>")}]

[{TS}]where[/]
  [dim](positional)[/]    {pos("left-path", "text")}                     [i]Path to the first monster.[/] [yellow](required)[/]                 
  [dim](positional)[/]    {pos("right-path", "text")}                    [i]Path to the second monster.[/] [yellow](required)[/]                
  [dim](pos. or opt.)[/]  {name("-o")}{dopt('|')}{name("--output-path")} {var("<text>")}              [i]Path to store the fused monster.[/] [yellow](required)[/]           
  [dim](option)[/]        {name("-c")}{dopt('|')}{name("--components")} {var("<text>")} [dim][[/]{dvar("<text>")}[dim] ...][/]  [i]Components to fuse.[/] [green](default: [/][green]['fang', 'claw'][/][green])[/]       
  [dim](option)[/]        {name("-a")}{dopt('|')}{name("--alpha")} {var("<float>")}                   [i]Weighting factor for the first monster.[/] [green](default: [/][green]0.5[/][green])[/]
  [dim](option)[/]        {dname("-?")}{dopt('|')}{dname("--help")}                            [i dim]Show this help message and exit.[/]                      
"""
    check_help_from_class(
        FusionConfig, "Fuse two monsters with polymerization.", "fuse.py", expected
    )


def test_dataclass_simple():
    @dataclass
    class FusionConfig:
        """
        Fusion config.

        Attributes:
            left_path: Path to the first monster.
            right_path: Path to the second monster.
            output_path: Path to store the fused monster.
            components: Components to fuse.
            alpha: Weighting factor for the first monster.
        """

        left_path: str
        right_path: str
        output_path: str
        components: list[str] = field(default_factory=lambda: ["fang", "claw"])
        alpha: float = 0.5

    expected = f"""\

Fuse two monsters with polymerization.

[{TS}]Usage:[/]
  fuse.py [{NS} {OS}]--left-path[/] [{VS}]<text>[/] [{NS} {OS}]--right-path[/] [{VS}]<text>[/] [{NS} {OS}]--output-path[/] [{VS}]<text>[/] [[{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]] [[{NS} {OS}]--alpha[/] [{VS}]<float>[/]]

[{TS}]where[/]
  [dim](pos. or opt.)[/]  [{NS} {OS}]-l[/][{OS} dim]|[/][{NS} {OS}]--left-path[/] [{VS}]<text>[/]                [i]Path to the first monster.[/] [yellow](required)[/]                 
  [dim](pos. or opt.)[/]  [{NS} {OS}]-r[/][{OS} dim]|[/][{NS} {OS}]--right-path[/] [{VS}]<text>[/]               [i]Path to the second monster.[/] [yellow](required)[/]                
  [dim](pos. or opt.)[/]  [{NS} {OS}]-o[/][{OS} dim]|[/][{NS} {OS}]--output-path[/] [{VS}]<text>[/]              [i]Path to store the fused monster.[/] [yellow](required)[/]           
  [dim](pos. or opt.)[/]  [{NS} {OS}]-c[/][{OS} dim]|[/][{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]  [i]Components to fuse.[/] [green](default: [/][green]['fang', 'claw'][/][green])[/]       
  [dim](pos. or opt.)[/]  [{NS} {OS}]-a[/][{OS} dim]|[/][{NS} {OS}]--alpha[/] [{VS}]<float>[/]                   [i]Weighting factor for the first monster.[/] [green](default: [/][green]0.5[/][green])[/]
  [dim](option)[/]        [{NS} {OS} dim]-?[/][{OS} dim]|[/][{NS} {OS} dim]--help[/]                            [i dim]Show this help message and exit.[/]                      
"""
    check_help_from_class(
        FusionConfig, "Fuse two monsters with polymerization.", "fuse.py", expected
    )


def test_nargs():
    def count_chars(
        words: list[str],
        /,
        *,
        extra_words: list[str] = [],
        verbose: bool = False,
    ) -> None:
        """
        Count the characters in a list of words.

        Some additional explanation in a new paragraph.

        Args:
            words: List of words to count characters in.
            extra_words: Extra words to count characters in.
            verbose: If true, print extra information.
        """
        pass

    def count_chars2(
        words: list[str],
        /,
        *,
        extra_words: list[str] = [],
        verbose: bool = False,
    ) -> None:
        """
        Count the characters
        in a list of words.

        Some additional explanation
        in a new paragraph.

        Args:
            words: List of words to count characters in.
            extra_words: Extra words to count characters in.
            verbose: If true, print extra information.
        """
        pass

    def count_chars3(
        words: list[str],
        /,
        *,
        extra_words: Annotated[list[str], "some metadata"] = [],
        verbose: bool = False,
    ) -> None:
        """
        Count the characters
        in a list of words.

        Some additional explanation
        in a new paragraph.

        Args:
            words: List of words to count characters in.
            extra_words: Extra words to count characters in.
            verbose: If true, print extra information.
        """
        pass

    expected = f"""\

Count the characters in a list of words.

Some additional explanation in a new paragraph.

[{TS}]Usage:[/]
  count_chars.py {pos("words", "text")} [dim][[/]{dpos("words", "text")}[dim] ...][/] [{name("--extra-words")} {var("<text>")} [dim][[/]{dvar("<text>")}[dim] ...][/]] [{name("--verbose")}]

[{TS}]where[/]
  [dim](positional)[/]  {pos("words", "text")} [dim][[/]{dpos("words", "text")}[dim] ...][/]       [i]List of words to count characters in.[/] [yellow](required)[/] 
  [dim](option)[/]      {name("-e")}{dopt("|")}{name("--extra-words")} {var("<text>")} [dim][[/]{dvar("<text>")}[dim] ...][/]  [i]Extra words to count characters in.[/] [green](default: [/][green][][/][green])[/]
  [dim](option)[/]      {name("-v")}{dopt("|")}{name("--verbose")}                          [i]If true, print extra information.[/] [green](flag)[/]         
  [dim](option)[/]      {dname("-?")}{dopt("|")}{dname("--help")}                             [i dim]Show this help message and exit.[/]                 
"""

    check_help_from_func(count_chars, "count_chars.py", expected)
    check_help_from_func(count_chars2, "count_chars.py", expected)
    check_help_from_func(count_chars3, "count_chars.py", expected)


def ls1(index: int, /, path: Path, *args: str, dummy: float, **kwargs: int) -> None:
    """
    List directory contents.

    Args:
        index: Index of the command.
        path: Path to the directory.
        args: Arguments to pass to `ls`.
        dummy: Dummy argument.
        kwargs: Dummy keyword arguments.
    """
    pass


def ls2(index: int, /, path: Path, *args: str, dummy: float, **kwargs: int) -> None:
    """
    List directory contents.

    Args:
        index: Index of the command.
        path: Path to the directory.
        *args: Arguments to pass to `ls`.
        dummy: Dummy argument.
        **kwargs: Dummy keyword arguments.
    """
    pass


def ls3(index: int, /, path: Path, *args: str, dummy: float, **kwargs: int) -> None:
    """
    List directory contents.

    Args:
        index: Index of the
            command.
        path: Path to the directory.
        *args: Arguments to pass
            to `ls`.
        dummy: Dummy argument.
        **kwargs: Dummy keyword arguments.
    """
    pass


@mark.parametrize("ls", [ls1, ls2, ls3])
def test_ordering(ls: Callable):
    # Help order respects the order of the arguments in the signature:
    # 1. positional only
    # 2. positional or keyword
    # 3. variadic positional (*args)
    # 4. keyword only
    # 5. variadic keyword (**kwargs)
    # However, because startle displays "positional or keyword" arguments within
    # their "keyword"-like usage, below might be a bit counterintuitive at first
    # glance.

    expected = f"""\

List directory contents.

[{TS}]Usage:[/]
  examples/ls.py {pos("index", "int")} {name("--path")} {var("<path>")} [{pos("", "text")} [dim][[/]{dpos("", "text")}[dim] ...][/]] {name("--dummy")} {var("<float>")} [{name("--")}[cyan]<[/][cyan bold]key[/][cyan]>[/] {var("<int>")} [dim][[/]{dname("--")}[cyan dim]<[/][cyan dim bold]key[/][cyan dim]>[/][dim] [/]{dvar("<int>")}[dim] ...][/]]

[{TS}]where[/]
  [dim](positional)[/]    {pos("index", "int")}            [i]Index of the command.[/] [yellow](required)[/]                         
  [dim](pos. or opt.)[/]  {name("-p")}{dopt("|")}{name("--path")} {var("<path>")}       [i]Path to the directory.[/] [yellow](required)[/]                        
  [dim](positional)[/]    {pos("", "text")} [dim][[/]{dpos("", "text")}[dim] ...][/]  [i]Arguments to pass to `ls`.[/] [cyan](unknown positional arguments)[/]
  [dim](option)[/]        {name("-d")}{dopt("|")}{name("--dummy")} {var("<float>")}     [i]Dummy argument.[/] [yellow](required)[/]                               
  [dim](option)[/]        {name("--")}[cyan]<[/][cyan bold]key[/][cyan]>[/] {var("<int>")}          [i]Dummy keyword arguments.[/] [cyan](unknown options)[/]               
  [dim](option)[/]        {dname("-?")}{dopt("|")}{dname("--help")}              [i dim]Show this help message and exit.[/]                         
"""

    check_help_from_func(ls, "examples/ls.py", expected)
