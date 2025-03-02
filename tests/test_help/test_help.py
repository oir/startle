from dataclasses import dataclass, field

from ._utils import NS, OS, TS, VS, check_help_from_class, check_help_from_func


def test_func_simple():
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

    def fusion2(
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
  fuse.py [{VS}]<[{NS}]left-path:[/]text>[/] [{VS}]<[{NS}]right-path:[/]text>[/] [{NS} {OS}]--output-path[/] [{VS}]<text>[/] [[{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]] [[{NS} {OS}]--alpha[/] [{VS}]<float>[/]]

[{TS}]where[/]
  [dim](positional)[/]    [{VS}]<[{NS}]left-path:[/]text>[/]                     [i]Path to the first monster.[/] [yellow](required)[/]                 
  [dim](positional)[/]    [{VS}]<[{NS}]right-path:[/]text>[/]                    [i]Path to the second monster.[/] [yellow](required)[/]                
  [dim](pos. or opt.)[/]  [{NS} {OS}]-o[/][{OS} dim]|[/][{NS} {OS}]--output-path[/] [{VS}]<text>[/]              [i]Path to store the fused monster.[/] [yellow](required)[/]           
  [dim](option)[/]        [{NS} {OS}]-c[/][{OS} dim]|[/][{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]  [i]Components to fuse.[/] [green](default: ['fang', 'claw'])[/]       
  [dim](option)[/]        [{NS} {OS}]-a[/][{OS} dim]|[/][{NS} {OS}]--alpha[/] [{VS}]<float>[/]                   [i]Weighting factor for the first monster.[/] [green](default: 0.5)[/]
  [dim](option)[/]        [{NS} {OS} dim]-?[/][{OS} dim]|[/][{NS} {OS} dim]--help[/]                            [i dim]Show this help message and exit.[/]                      
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
  fuse.py [{VS}]<[{NS}]left-path:[/]text>[/] [{VS}]<[{NS}]right-path:[/]text>[/] [{NS} {OS}]--output-path[/] [{VS}]<text>[/] [[{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]] [[{NS} {OS}]--alpha[/] [{VS}]<float>[/]]

[{TS}]where[/]
  [dim](positional)[/]    [{VS}]<[{NS}]left-path:[/]text>[/]                     [i]Path to the first monster.[/] [yellow](required)[/]                 
  [dim](positional)[/]    [{VS}]<[{NS}]right-path:[/]text>[/]                    [i]Path to the second monster.[/] [yellow](required)[/]                
  [dim](pos. or opt.)[/]  [{NS} {OS}]-o[/][{OS} dim]|[/][{NS} {OS}]--output-path[/] [{VS}]<text>[/]              [i]Path to store the fused monster.[/] [yellow](required)[/]           
  [dim](option)[/]        [{NS} {OS}]-c[/][{OS} dim]|[/][{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]  [i]Components to fuse.[/] [green](default: ['fang', 'claw'])[/]       
  [dim](option)[/]        [{NS} {OS}]-a[/][{OS} dim]|[/][{NS} {OS}]--alpha[/] [{VS}]<float>[/]                   [i]Weighting factor for the first monster.[/] [green](default: 0.5)[/]
  [dim](option)[/]        [{NS} {OS} dim]-?[/][{OS} dim]|[/][{NS} {OS} dim]--help[/]                            [i dim]Show this help message and exit.[/]                      
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
  [dim](pos. or opt.)[/]  [{NS} {OS}]-c[/][{OS} dim]|[/][{NS} {OS}]--components[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]  [i]Components to fuse.[/] [green](default: <factory>)[/]              
  [dim](pos. or opt.)[/]  [{NS} {OS}]-a[/][{OS} dim]|[/][{NS} {OS}]--alpha[/] [{VS}]<float>[/]                   [i]Weighting factor for the first monster.[/] [green](default: 0.5)[/]
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

        Args:
            words: List of words to count characters in.
            extra_words: Extra words to count characters in.
            verbose: If true, print extra information.
        """
        for word in words:
            print(f"{word}: {len(word)}")
        if verbose:
            for word in extra_words:
                print(f"{word}: {len(word)}")

    expected = f"""\

Count the characters in a list of words.

[{TS}]Usage:[/]
  count_chars.py [{VS}]<[{NS}]words:[/]text>[/] [dim][[/][{VS} dim]<[{NS}]words:[/]text>[/][dim] ...][/] [[{NS} {OS}]--extra-words[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]] [[{NS} {OS}]--verbose[/]]

[{TS}]where[/]
  [dim](positional)[/]  [{VS}]<[{NS}]words:[/]text>[/] [dim][[/][{VS} dim]<[{NS}]words:[/]text>[/][dim] ...][/]       [i]List of words to count characters in.[/] [yellow](required)[/] 
  [dim](option)[/]      [{NS} {OS}]-e[/][{OS} dim]|[/][{NS} {OS}]--extra-words[/] [{VS}]<text>[/] [dim][[/][{VS} dim]<text>[/][dim] ...][/]  [i]Extra words to count characters in.[/] [green](default: [])[/]
  [dim](option)[/]      [{NS} {OS}]-v[/][{OS} dim]|[/][{NS} {OS}]--verbose[/][{OS} dim]                        [/]  [i]If true, print extra information.[/] [green](flag)[/]         
  [dim](option)[/]      [{NS} {OS} dim]-?[/][{OS} dim]|[/][{NS} {OS} dim]--help[/]                             [i dim]Show this help message and exit.[/]                 
"""

    check_help_from_func(count_chars, "count_chars.py", expected)
