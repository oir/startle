from typing import Callable

from rich.console import Console

from startle.inspector import make_args

vs = "blue"
ns = "bold"
os = "green"
ts = "bold underline dim"


def check_help(f: Callable, program_name: str, expected: str):
    console = Console(width=120, highlight=False)
    with console.capture() as capture:
        make_args(f).print_help(console, program_name)
    result = capture.get()

    console = Console(width=120, highlight=False)
    with console.capture() as capture:
        console.print(expected)
    expected = capture.get()

    assert result == expected


def test_simple():
    def fusion(
        left_path: str,
        right_path: str,
        /,
        output_path: str,
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

    expected = f"""\
Fuse two monsters with polymerization.

[{ts}]Usage:[/]
  fuse.py [{vs}]<[{ns}]left-path:[/]text>[/] [{vs}]<[{ns}]right-path:[/]text>[/] [{ns} {os}]--output-path[/] [{vs}]<text>[/] [[{ns} {os}]--components[/] [{vs}]<text> [dim][<text> ...][/][/]] [[{ns} {os}]--alpha[/] [{vs}]<float>[/]]

[{ts}]where[/]
  [dim](positional)[/]    [{vs}]<[{ns}]left-path:[/]text>[/]                     [i]Path to the first monster.[/] [yellow](required)[/]                 
  [dim](positional)[/]    [{vs}]<[{ns}]right-path:[/]text>[/]                    [i]Path to the second monster.[/] [yellow](required)[/]                
  [dim](pos. or opt.)[/]  [{ns} {os}]-o[/][{os} dim]|[/][{ns} {os}]--output-path[/] [{vs}]<text>[/]              [i]Path to store the fused monster.[/] [yellow](required)[/]           
  [dim](option)[/]        [{ns} {os}]-c[/][{os} dim]|[/][{ns} {os}]--components[/] [{vs}]<text> [dim][<text> ...][/][/]  [i]Components to fuse.[/] [green](default: ['fang', 'claw'])[/]       
  [dim](option)[/]        [{ns} {os}]-a[/][{os} dim]|[/][{ns} {os}]--alpha[/] [{vs}]<float>[/]                   [i]Weighting factor for the first monster.[/] [green](default: 0.5)[/]"""

    check_help(fusion, "fuse.py", expected)
