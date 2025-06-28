import sys
from dataclasses import dataclass, field

from .args import Args
from .error import ParserConfigError, ParserOptionError


@dataclass
class Cmds:
    """
    A parser class which is a collection of Args objects paired with a command.

    Parsing is done by treating the first argument as a command and then
    passing the remaining arguments to the Args object associated with that
    command.
    """

    cmd_parsers: dict[str, Args] = field(default_factory=dict)
    brief: str = ""
    program_name: str = ""

    def get_cmd_parser(
        self, cli_args: list[str] | None = None, *, default: str | None = None
    ) -> tuple[str, Args, list[str]]:
        cli_args = cli_args if cli_args is not None else sys.argv[1:]

        if default is not None and default not in self.cmd_parsers:
            raise ParserConfigError(
                f"Default command `{default}` is not among the subcommands!"
            )

        if not cli_args and default is None:
            raise ParserOptionError("No command given!")

        if cli_args:
            cmd = cli_args[0]
            if cmd in ["-?", "--help"]:
                self.print_help()
                raise SystemExit(0)

            if cmd not in self.cmd_parsers:
                if default is None:
                    raise ParserOptionError(f"Unknown command `{cmd}`!")
                return default, self.cmd_parsers[default], cli_args

            return cmd, self.cmd_parsers[cmd], cli_args[1:]

        assert default is not None, "Programming error!"

        return default, self.cmd_parsers[default], cli_args

    def print_help(self, console=None, usage_only: bool = False) -> None:
        """
        Print the help message to the console.

        Args:
            console: A rich console to print to. If None, uses the default console.
            usage_only: Whether to print only the usage line.
        """
        import sys

        from rich.console import Console
        from rich.table import Table
        from rich.text import Text

        name = self.program_name or sys.argv[0]

        sty_pos_name = "bold"
        sty_opt = "green"
        sty_var = "blue"
        sty_title = "bold underline dim"
        sty_help = "italic"

        console = console or Console()
        if self.brief and not usage_only:
            console.print(self.brief + "\n")

        console.print(
            Text.assemble(
                "\n",
                ("Usage:", sty_title),
                "\n",
                f"  {name} ",
                ("<", sty_var),
                ("command", f"{sty_var} {sty_pos_name}"),
                (">", sty_var),
                " ",
                ("<command-specific-args>", sty_var),
                "\n",
            )
        )

        console.print(Text("Commands:", style=sty_title))

        table = Table(show_header=False, box=None, padding=(0, 0, 0, 2))
        for cmd, args in self.cmd_parsers.items():
            brief = args.brief.split("\n\n")[0]
            table.add_row(
                Text(cmd, style=f"{sty_pos_name} {sty_var}"),
                Text(brief, style=sty_help),
            )
        console.print(table)

        console.print(
            Text.assemble(
                "\n",
                ("Run ", "dim"),
                "`",
                name,
                " ",
                ("<", sty_var),
                ("command", f"{sty_var} {sty_pos_name}"),
                (">", sty_var),
                " ",
                ("--help", f"{sty_opt}"),
                "`",
                (" to see all command-specific options.", "dim"),
                "\n",
            )
        )
