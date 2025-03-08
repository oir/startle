import subprocess
from pathlib import Path

from startle import start


def run_cmd(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def ls(index: int, /, path: Path, *args, dummy: float, **kwargs) -> None:
    """
    List directory contents.

    Args:
        *args: Arguments to pass to `ls`.
    """
    run_cmd(["ls", *args])


start(ls)
