from typing import Callable, TypeVar

from .inspector import make_args

T = TypeVar("T")


def start(func: Callable[..., T], args: list[str] | None = None) -> T:
    args_ = make_args(func)
    args_.parse(args)
    f_args, f_kwargs = args_.make_func_args()
    return func(*f_args, **f_kwargs)
