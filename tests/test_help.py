from startle.inspector import make_args

from rich.console import Console

vs = "blue"
ns = "bold green"
ts = "bold underline dim"


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

    args = make_args(fusion)
    console = Console(width=120, highlight=False)
    with console.capture() as capture:
        args.print_help(console, "fuse.py")
    result = capture.get()

    expected = f"""\
Fuse two monsters with polymerization.

[{ts}]Usage:[/]
  fuse.py [{vs}]<[/][{ns}]left-path:[/][{vs}]text>[/] [{vs}]<[/][{ns}]right-path:[/][{vs}]text>[/] [{ns}]--output-path[/] [{vs}]<text>[/] [[{ns}]--components[/] [{vs}]<text> [dim][<text> ...][/][/]] [[{ns}]--alpha[/] [{vs}]<float>[/]]

[{ts}]where[/]
  [dim](positional)[/]    [{vs}]<[/][{ns}]left-path:[/][{vs}]text>[/]                     [i]Path to the first monster.[/] [yellow](required)[/]                 
  [dim](positional)[/]    [{vs}]<[/][{ns}]right-path:[/][{vs}]text>[/]                    [i]Path to the second monster.[/] [yellow](required)[/]                
  [dim](pos. or opt.)[/]  [{ns}]-o[/],[{ns}]--output-path[/] [{vs}]<text>[/]              [i]Path to store the fused monster.[/] [yellow](required)[/]           
  [dim](option)[/]        [{ns}]-c[/],[{ns}]--components[/] [{vs}]<text> [dim][<text> ...][/][/]  [i]Components to fuse.[/] [green](default: ['fang', 'claw'])[/]       
  [dim](option)[/]        [{ns}]-a[/],[{ns}]--alpha[/] [{vs}]<float>[/]                   [i]Weighting factor for the first monster.[/] [green](default: 0.5)[/]"""

    console = Console(width=120, highlight=False)
    with console.capture() as capture:
        console.print(expected)
    expected = capture.get()

    assert result == expected
