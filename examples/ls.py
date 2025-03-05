import subprocess

from startle import start


def run_cmd(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def ls(*args: str) -> None:
    """
    List directory contents.

    Args:
        *args: Arguments to pass to `ls`.
    """
    run_cmd(["ls", *args])


start(ls)
