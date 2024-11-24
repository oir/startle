from startle import start


def add(a: int, b: int) -> None:
    """
    Add two numbers.

    Args:
        a: The first number.
        b: The second number.
    """
    print(f"{a} + {b} = {a + b}")


def sub(a: int, b: int) -> None:
    """
    Subtract two numbers.

    Args:
        a: The first number.
        b: The second number
    """
    print(f"{a} - {b} = {a - b}")


def mul(a: int, b: int) -> None:
    """
    Multiply two numbers.

    Args:
        a: The first number.
        b: The second number.
    """
    print(f"{a} * {b} = {a * b}")


def div(a: int, b: int) -> None:
    """
    Divide two numbers.

    Args:
        a: The dividend.
        b: The divisor.
    """
    print(f"{a} / {b} = {a / b}")


if __name__ == "__main__":
    start([add, sub, mul, div])
