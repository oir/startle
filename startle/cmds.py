import sys
from dataclasses import dataclass, field

from .args import Args
from .error import ParserOptionError


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

    def get_cmd_parser(self, cli_args: list[str]) -> tuple[str, Args, list[str]]:
        cli_args = cli_args or sys.argv[1:]

        if not cli_args:
            raise ParserOptionError("No command given!")

        cmd = cli_args[0]
        if cmd in ["-?", "--help"]:
            self.print_help()
            raise SystemExit(0)

        if cmd not in self.cmd_parsers:
            raise ParserOptionError(f"Unknown command `{cmd}`!")

        return cmd, self.cmd_parsers[cmd], cli_args[1:]

    def parse(self, cli_args: list[str] | None = None) -> tuple[str, Args]:
        cli_args = cli_args or sys.argv[1:]

        cmd, args, remaining_cli_args = self.get_cmd_parser(cli_args)
        args.parse(remaining_cli_args)
        return cmd, args

    def print_help(
        self, console=None, program_name: str | None = None, usage_only: bool = False
    ) -> None:
        """
        Print the help message to the console.

        Args:
            console: A rich console to print to. If None, uses the default console.
            program_name: The name of the program to use in the help message.
            usage_only: Whether to print only the usage line.
        """
        import sys

        from rich.console import Console
        from rich.table import Table
        from rich.text import Text

        name = program_name or sys.argv[0]

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
