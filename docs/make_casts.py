"""
Generate asciinema v2 .cast files for the docs page without recording a live
terminal session.

Run from the repo root:
    python docs/make_casts.py
"""

import io
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from rich.console import Console

from startle._inspect.make_args import make_args_from_func


@dataclass
class DBConfig:
    """
    Attributes:
        host: Database hostname.
        port: Database port.
    """

    host: str = "localhost"
    port: int = 5432


@dataclass
class ServerConfig:
    """
    Attributes:
        db: Database configuration.
        workers: Number of workers.
    """

    db: DBConfig = field(default_factory=DBConfig)
    workers: int = 4


def serve(server: ServerConfig) -> None:
    """Run a server."""


@dataclass
class RandomForestConfig:
    """
    Configuration for the RandomForestClassifier.

    Attributes:
        n_estimators: The number of trees in the forest.
        criterion: The function to measure the quality of a split.
        max_depth: The maximum depth of the tree.
    """

    n_estimators: int = 100
    criterion: Literal["gini", "entropy"] = "gini"
    max_depth: int | None = None


@dataclass
class DatasetConfig:
    """
    Configuration for the dataset split.

    Attributes:
        test_size: The proportion of the dataset to include in the test split.
        shuffle: Whether or not to shuffle the data before splitting.
    """

    test_size: float = 0.5
    shuffle: bool = True


def fit_rf(
    model_config: RandomForestConfig,
    dataset_config: DatasetConfig,
    *,
    quiet: bool = False,
    output_file: Path | None = None,
):
    """
    Fit a RandomForestClassifier on the digits dataset and print the classification report.

    Args:
        model_config: Configuration for the RandomForestClassifier.
        dataset_config: Configuration for the dataset split.
        quiet: If True, suppress output.
        output_file: Optional path to save the output.
    """


PROMPT = "❯ "


def _capture_help(
    func: Callable[..., Any],
    program_name: str,
    naming: Literal["flat", "nested"],
    width: int,
    render_width: int | None = None,
) -> str:
    """
    Render help with Rich.

    `width` is the terminal/cast width (each line is padded to this).
    `render_width` (optional) is the logical width Rich uses for layout —
    set smaller than `width` to leave trailing whitespace on the right,
    which prevents visible content from being clipped when the player
    overflows the docs container by a few pixels.
    """

    args = make_args_from_func(
        func, program_name=program_name, recurse=True, naming=naming
    )
    buf = io.StringIO()
    rw = render_width if render_width is not None else width
    console = Console(
        file=buf, force_terminal=True, color_system="standard", width=rw
    )
    args.print_help(console=console)
    out = buf.getvalue()
    if rw < width:
        pad = " " * (width - rw)
        parts: list[str] = []
        for line in out.splitlines(keepends=True):
            if line.endswith("\n"):
                parts.append(line[:-1] + pad + "\n")
            else:
                parts.append(line + pad)
        out = "".join(parts)
    return out


def _build_cast(command: str, output: str, width: int) -> str:
    rows = output.count("\n") + 2
    header = {
        "version": 2,
        "width": width,
        "height": rows,
        "env": {"SHELL": "/bin/fish", "TERM": "xterm-256color"},
    }

    events: list[tuple[float, str, str]] = []
    t = 0.01
    events.append((round(t, 6), "o", "\x1b[?1034h" + PROMPT))
    for ch in command:
        t += 0.17
        events.append((round(t, 6), "o", ch))
    t += 0.3
    events.append((round(t, 6), "o", "\r\n"))
    t += 0.05
    events.append((round(t, 6), "o", output.replace("\n", "\r\n")))
    t += 0.3
    events.append((round(t, 6), "o", PROMPT))

    lines = [json.dumps(header)]
    for ev in events:
        lines.append(json.dumps(list(ev)))
    return "\n".join(lines) + "\n"


def main() -> None:
    cast_dir = Path(__file__).parent / "cast"
    width = 103

    for naming in ("flat", "nested"):
        output = _capture_help(serve, "serve.py", naming, width)
        cast = _build_cast("python serve.py --help", output, width)
        path = cast_dir / f"recurse-help-{naming}.cast"
        path.write_text(cast)
        print(f"wrote {path.relative_to(Path.cwd())}")

    output = _capture_help(fit_rf, "digits.py", "flat", width, render_width=90)
    cast = _build_cast("python digits.py --help", output, width)
    path = cast_dir / "digits-help.cast"
    path.write_text(cast)
    print(f"wrote {path.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
