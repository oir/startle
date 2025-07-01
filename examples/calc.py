from startle import start


def add(ns: list[int]) -> None:
    """
    Add numbers together.

    Args:
        ns: The numbers to add together.
    """
    total = sum(ns)
    print(f"{' + '.join(map(str, ns))} = {total}")


def sub(a: int, b: int) -> None:
    """
    Subtract a number from another.

    Args:
        a: The first number.
        b: The second number
    """
    print(f"{a} - {b} = {a - b}")


def mul(ns: list[int]) -> None:
    """
    Multiply numbers together.

    Args:
        ns: The numbers to multiply together.
    """
    total = 1
    for n in ns:
        total *= n
    print(f"{' * '.join(map(str, ns))} = {total}")


def div(a: int, b: int) -> None:
    """
    Divide a number by another.

    Args:
        a: The dividend.
        b: The divisor.
    """
    print(f"{a} / {b} = {a / b}")


if __name__ == "__main__":
    start([add, sub, mul, div], default="add")
