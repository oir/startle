from typing import Callable

from .inspector import make_args


def start(func: Callable):
    args = make_args(func)
    args.parse()
    f_args, f_kwargs = args.make_func_args()
    func(*f_args, **f_kwargs)
