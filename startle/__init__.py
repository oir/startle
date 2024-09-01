from typing import Callable
from .inspector import make_args
from ._version import __version__


def start(func: Callable):
    args = make_args(func)
    args.parse()
    args_, kwargs_ = args.make_func_args()
    print(args_, kwargs_)
    func(*args_, **kwargs_)
