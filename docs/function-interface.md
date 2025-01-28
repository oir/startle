# CLI from functions

`start()` function translates a given Python function's interface to a 
command-line interface.
It does so by inspecting the given function and defining the command-line arguments and options
based on the function arguments (with their type hints and default values) and the docstring.

More specifically, when you invoke `start(f)`, for a function `f`, it will
- construct an argument parser (based on `f`'s argument type hints, defaults, and docstring),
- parse the command-line arguments, i.e. process raw command-line strings and construct objects
  based on the provided type hints,
- provide the parsed objects as arguments to `f`, and _invoke_ it.

## Example with walkthrough

Let us revisit the main example to make the above concepts more concrete.

<div class="code-file" style="--filename:'wc.py'">


```python
from pathlib import Path
from typing import Literal

from startle import start


def word_count(
    fname: Path, /, kind: Literal["word", "char"] = "word", *, verbose: bool = False
) -> None:
    """
    Count the number of words or characters in a file.

    Args:
        fname: The file to count.
        kind: Whether to count words or characters.
        verbose: Whether to print additional info.
    """

    text = open(fname).read()
    count = len(text.split()) if kind == "word" else len(text)

    print(f"{count} {kind}s in {fname}" if verbose else count)


start(word_count)
```

</div>

Assume we run our file from the command-line as:
```bash
python wc.py wc.py -k char --verbose
```

Then `start(word_count)` will first inspect the `word_count()` function
to construct an argument parser object `Args` which will look like:

```python
Args(brief='Count the number of words or characters in a file.',
     program_name='',
     _positional_args=[Arg(name=Name(short='', long='fname'),
                           type_=<class 'pathlib.Path'>,
                           is_positional=True,
                           is_named=False,
                           is_nary=False,
                           help='The file to count.',
                           metavar='path',
                           default=None,
                           required=True),
                       Arg(name=Name(short='k', long='kind'),
                           type_=typing.Literal['word', 'char'],
                           is_positional=True,
                           is_named=True,
                           is_nary=False,
                           help='Whether to count words or characters.',
                           metavar=['word', 'char'],
                           default='word',
                           required=False)],
     _named_args=[Arg(name=Name(short='k', long='kind'),
                      type_=typing.Literal['word', 'char'],
                      is_positional=True,
                      is_named=True,
                      is_nary=False,
                      help='Whether to count words or characters.',
                      metavar=['word', 'char'],
                      default='word',
                      required=False),
                  Arg(name=Name(short='v', long='verbose'),
                      type_=<class 'bool'>,
                      is_positional=False,
                      is_named=True,
                      is_nary=False,
                      help='Whether to print additional info.',
                      metavar=['true', 'false'],
                      default=False,
                      required=False)])
```
_(Some fields are omitted for illustration.)_

Our function signature (simplified of type hints) looks like:

<div class="ascii">

```python
def word_count(fname, /, kind, *, verbose):
    """        ┬────     ─┬──     ─────┬─
               │          │            │
               │      Positional       │
               │      or keyword       ╰ Keyword only
               │
               ╰─ Positional only                     """
```

</div>

with the delimiters `/` and `*`.

As a result, we see that the resulting `Args` object contains two
positional arguments (one for `fname`, and one for `kind`), and
two named arguments / options (one for `kind`, and one for `verbose`).
Note that `kind`, given that it is declared "positional _or_ keyword",
appears in both lists as expected, whereas `fname` becomes a positional-only
argument and `verbose` becomes named-only argument (or option).

Further observe how the `Arg` objects have their assigned `type_`s
based on the hints in `word_count()`, as well as their default values
(which determines if an argument is required or optional), and
their `help` strings.

Once the `Args` parser is constructed, `Args.parse()` will be invoked using
the command line arguments we specified: `["myfile.txt", "-k", "char", "--verbose"]`

This will result in the following _parsed_ objects for each argument:
- ```python
  Arg(name=Name(short='', long='fname'), ..., _value=PosixPath('myfile.txt'))
  ```
- ```python
  Arg(name=Name(short='k', long='kind'), ..., _value='char')
  ```
- ```python
  Arg(name=Name(short='v', long='verbose'), ..., _value=True)
  ```
Observe how internal `_value` fields contain the concrete parsed values.

Finally, these values are translated into appropriate positional and keyword
arguments as `word_count` expects them, and the function is called:
```python
f_args = [PosixPath('myfile.txt'), 'char']
f_kwargs = {"verbose": True}
word_count(*f_args, **f_kwargs)
```

This gives us the final output:

<div id="wc-run-cast"></div>

## Commands

You can invoke `start()` with a list of functions instead of a single function.
In this case, functions are made available as _commands_ with their own arguments
and options in your CLI.

<div class="code-file" style="--filename:'calc.py'">

```python
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
    start([add, sub, mul, div])

```

</div>

<div id="calc-cast"></div>

In the invocation `python calc.py add 1 2 3`, first argument is `add`, which causes the execution
to dispatch to the `add` command (i.e. `add()` function). The rest of the arguments (`1 2 3`) then
are passed along to `add()`.

You can rename commands by passing in a `dict[str, Callable]` instead of a
`list[Callable]`:

```python
start({
    "plus": add,
    "minus": sub,
    "times": mul,
    "div": div,
})
```
```bash
~ ❯ python program.py plus 1 2 3
```

## Returning

`start()`'s design is primarily around the use case where it invokes a function executing
the entire program.
However, for completeness, `start()` returns, and it returns the object returned by its
argument function.

This means it is possible to continue execution using the returned value
from `start()`:

<div class="code-file" style="--filename:'adder.py'">

```python
from startle import start

def add(numbers: list[int]) -> None:
    return sum(numbers)

if __name__ == "__main__":
    total = start(add)
    print(f"Computed {total}.")
```

</div>

<div id="adder-run-cast"></div>

<script>
AsciinemaPlayer.create('cast/wc-run.cast', document.getElementById('wc-run-cast'), {
    autoPlay: true,
    controls: true,
    rows: 3,
    terminalFontFamily: "'Fira Mono', monospace",
    terminalFontSize: "12px",
    fit: false,
    theme: "custom-auto",
});
AsciinemaPlayer.create('cast/calc.cast', document.getElementById('calc-cast'), {
    autoPlay: true,
    controls: true,
    rows: 27,
    terminalFontFamily: "'Fira Mono', monospace",
    terminalFontSize: "12px",
    fit: false,
    theme: "custom-auto",
});
AsciinemaPlayer.create('cast/adder-run.cast', document.getElementById('adder-run-cast'), {
    autoPlay: true,
    controls: true,
    speed: 2,
    rows: 3,
    terminalFontFamily: "'Fira Mono', monospace",
    terminalFontSize: "12px",
    fit: false,
    theme: "custom-auto",
});
</script>


