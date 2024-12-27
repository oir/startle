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

`wc.py`:
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

Assume we run our file from the command-line as:
```bash
python wc.py myfile.txt -k char --verbose
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
Observer how internal `_value` fields contain the concrete parsed values.

Finally, these values are translated into appropriate positional and keyword
arguments as `word_count` expects them, and the function is called:
```python
f_args = [PosixPath('myfile.txt'), 'char']
f_kwargs = {"verbose": True}
word_count(*f_args, **f_kwargs)
```

This gives us the final output:
```bash
~ ❯ python examples/wc.py myfile.txt -k char --verbose
590 chars in examples/wc.py
~ ❯
```

## Argument specification

This subsection provides more detail about how a function argument is translated
into a command-line argument for the parser.

### Name

Option names are obtained from the name of the argument in the function
definition, as is, except any `"_"` is replaced by `"-"`.

If the function argument 
name is long (more than 1 character), it is used as the "long" name of the option,
to be used with `--` prefix. In this case, first letter of the argument name is 
used to define the "short" name, if it's available.
If the function argument name is short (1 character), it is used as the "short"
name and the CLI argument will not have a long name.

Argument name is less important for positional arguments since it is not used
when passing it in, however it is still used as part of the help string.
Automatic short name is not generated for positional arguments since it is not
needed.

Some examples:
- ```python
  def magic_missile(direction: str, mana_cost: float):
  ```
  - `-d, --direction`
  - `-m, --mana-cost`
- ```python
  def magic_missile(missile_direction: str, mana_cost: float):
  ```
  - `-m, --missile-direction`
  - `--mana-cost`
- ```python
  def magic_missile(missile_direction: str, /, mana_cost: float):
  ```
  - `missile-direction`
  - `-m, --mana-cost`

### Type

Target type after parsing the argument is directly obtained from the type
hint assigned to the function argument.

See [Types and parsing rules](types#types-and-parsing-rules) for
detailed information on how each such type is parsed, and how new
types can be registered.

### Positional arg vs option

Python functions can (optionally) use `/` and `*` delimiters to
designate a function argument as a "positional only", "keyword only", or both.

<div class="ascii">

```python
def func(pos1, pos2, /, pos_or_kwd, *, kwd1, kwd2):
    """  ┬─────────     ────┬─────     ──────┬───
         │                  │                │
         │              Positional           │
         │              or keyword           ╰ Keyword only
         │
         ╰─ Positional only                     """
```

</div>

This directly translates into the same notion for command-line arguments.
Positonal only function arguments become positional command-line arguments,
and keyword only function arguments become command-line options.
Function arguments that are both become command-line arguments that could be
fed in either as a positional argument or an option, during command-line
invocation.

### Optional vs required

If a function argument has a default value assignment, as in
```python
def f(..., arg: type = value, ...): 
```
then the command-line argument becomes _optional_. If not provided, realized
value will have the default-assigned `value`.

If there is no default value assignment, like
```python
def f(..., arg: type, ...): 
```
then the command-line argument is _required_. If a required argument or option
is not provided at the command-line, then `start()` will error.

### Flags

Flags are options that do not admit a value, and fed in only using their name.
For example, `python program.py --opt` or `python program.py -o` as opposed to
regular options `python program.py --opt val`. Thus, flags work for the notion
of _toggling_, as the only two possible configurations it provides is to either
feed them in or not feed them in.

If a function argument has a type hint of `bool`, has a default value of `False`,
and is an option-only (keyword only) argument, then it becomes a flag. If any of
these three conditions do not hold, then it is not a flag.

In the [main example](/#showcase), `verbose` argument is a flag:
```python
def word_count(
    fname: Path, /, kind: Literal["word", "char"] = "word", *, verbose: bool = False
) -> None:
    ...
```
and hence `--verbose` is fed in its invocation as opposed to `--verbose true` or
`--verbose=true`:
```bash
~ ❯ python wc.py wc.py -k char --verbose
```

### Help 

Descriptions of arguments to be displayed when `--help` is invoked
are retrieved from the docstring of the function. To this end, docstring is
expected to follow the following format (with some leeway):

```python
def func(arg1: type1, arg2: type2, ..., argn: typen):
    """
    Some function.

    Some more detailed description of the function.

    Args:
        arg1: Description of arg1.
        arg2: Description of arg2
            which has some more detail here.
        arg3: arg3 help here.
        ...
    """
```

Part of the docstring until we observe either `"Args:"` or `"Returns:"` make up
the brief of the overall program. Individual descriptions under the `Args:`
section, such as `"Description of arg1."` will constitute the help text specific
to that argument.

Help descriptions are optional. When docstring is unavailable, or parsing the
desired form fails, help text will be empty (rather than raising an error).

### Metavar 

Metavar is the illustratory variable name of an argument that is
substituted by the actual value in its place when it's fed in from the command-line.
This is determined by the type of the argument as defined in the type hint.

For instance type `str` has a metavar `text`, which means for an option with
name `arg`, the help string will display `--arg <text>`, and for a positional
argument, it will display `<arg:text>`. 

See [Types and parsing rules](types#types-and-parsing-rules) for
the predefined mapping of types to metavars, and how new metavars can be
registered.

### Unary vs n-ary

Unary arguments are constructed from a single command-line string value in the
argument list (as in, a single string item in the list `sys.argv`):
```bash
python myprogram.py --opt value
```

Whereas _n-ary_ arguments admit multiple such values:
```bash
python myprogram.py --opt value1 value2 value3
```
or 
```bash
python myprogram.py --opt=value1 --opt=value2 --opt=value3
```
This is similar to the `nargs` option in the native `argparse` module.

Unary vs n-ary distinction is determined by the type hint designated with
the function argument. Most types define a unary argument whereas a
`list[T]`, a `set[T]`, or a `tuple[T, ...]` (with a literal `Ellipsis` constant)
will result in an _n-ary_ argument of type `T`.
This means each individual value that's fed in, e.g.
`value2`, will be attempted to be parsed as a `T` and appended to the
container.

See [Types and parsing rules](types#types-and-parsing-rules) for detail,
and the example [cat.py](https://github.com/oir/startle/blob/main/examples/cat.py)
for an illustration.

### Choices

Sometimes it is desirable to limit the possible values for an argument or an option
to a number of choices, and reject any other value by erroring out.

In **startle**, similar to _unary_-ness or _flag_-ness, this is handled by the
type hints corresponding to the argument. If the type is a `typing.Literal` of
strings, e.g. `Literal["a", "b", "c"]`, or an `Enum` class (a user type deriving
from `enum.Enum`), allowed types will be limited to the specific options.

For example:<br>
`program.py:`
```python
from typing import Literal
from startle import start

def hello(to: Literal["world", "terra", "earth"]):
    print(f"hello {to}")

start(hello)
```
```bash
~ ❯ python program.py world
hello world
~ ❯ python program.py mars
Error: Cannot parse literal ('world', 'terra', 'earth') from `mars`!
...
~ ❯
```

This is similar to the `choices` configuration in the native `argparse` module of Python.

See [Types and parsing rules](types#types-and-parsing-rules) for more detail, and
examples [color.py](https://github.com/oir/startle/blob/main/examples/color.py) and
[wc.py](https://github.com/oir/startle/blob/main/examples/wc.py) for more showcases.


### Unknown arguments and options

Normally, unexpected or unrecognized arguments fed in from the command-line
will result in an error during parsing time. However, `start()` provides you
the possibility of allowing them and parsing them by using `*args` and `**kwargs`
arguments to your function.

**Unknown arguments:** If your function has `*args` in the argument list to
make it admit any positional argument, this in turn will make your program
admit any unrecognized command-line arguments and store them in `args` variable.

This is similar to the `parse_unknown_args()` of the native `argparse` module.

An example: <br>
`program.py`:
```python
from startle import start

def f(*args):
    print(args)

start(f)
```
```bash
~ ❯ python program.py fireball --kind red hot --mana-cost=30
('fireball', '--kind', 'red', 'hot', '--mana-cost=30')
~ ❯ 
```

Observe that _everything_ unknown is fed into `args` as unknown _positional_
argument strings, including strings that conventionally look like option names
such as `--kind`.

**Unknown options:** If your function has **kwargs** in the argument list to
admit any unknown keyword argument, then your program will admit any unrecognized
command-line option, and store them in `kwargs` variable.

Since unknown option names by definition are undefined, a string such as `--kind`
is technically ambiguous: It could refer to the _name_ of an unknown option, or
a _value_ for a preceding option name or a positional argument. In the case
of unknown options, `start()` will assume this refers to an unknown option name,
and a best effort parsing is performed to determine unknown option names and values.
Any string that could be interpreted as an option name will be parsed as an unknown
option name. Any string that could not be interpreted as an option name will be parsed
as a value to the option preceding the value.

An example:<br>
`program.py`:
```python
from startle import start

def f(**kwargs):
    print(kwargs)

start(f)
```
```bash
~ ❯ python program.py --kind red hot --mana-cost=30 -d up
{'kind': ['red', 'hot'], 'mana_cost': '30', 'd': 'up'}
~ ❯ 
```

When multiple _value_-like strings is matched to the same _name_-like string, the
values are gathered in a list, as if the option was n-ary. If not, they stand as strings.

In the above, `"red"` and `"hot"` follow `"--kind"`, which resulted in `kwargs["kind"]` to
be the list `["red", "hot"]`. In contrast, `kwargs["mana_cost"]` and `kwargs["d"]` are
merely `str`s. 


> [!WARNING]
> Note that unlike "unknown arguments", "unknown options" can _fail_ to parse:
> ```bash
> ~ ❯ python program.py fireball --kind red hot --mana-cost=30
> Error: Unexpected positional argument: `fireball`!
> ```
> This is because there is no way to associate `"fireball"` with any _name_-like keyword,
> and `**kwargs` implies _keyword only_ unknown arguments to our function.

**Unknown arguments _and_ options:** The above failure can be worked around if we admit
both unknown arguments, and options, i.e. if our function has both `*args`, and `**kwargs`
listed:

`program.py`:
```python
from startle import start

def f(*args, **kwargs):
    print(args)
    print(kwargs)

start(f)
```
```bash
~ ❯ python program.py fireball --kind red hot --mana-cost=30
('fireball',)
{'kind': ['red', 'hot'], 'mana_cost': '30'}
~ ❯
```

In this case, unrecognized command-line argument strings are first
attempted to be parsed as key-value items for `kwargs`, and if that
fails, they will be appended to `args`.

(`kwargs` is prioritized over `args` because otherwise everything
would always fall into `args` and `kwargs` would always be empty.)


## Commands

You can invoke `start()` with a list of functions instead of a single function.
In this case, functions are made available as _commands_ with their own arguments
and options in your CLI.

For example:
```python
from startle import start

def func1(...):
    ...

def func2(...):
    ...

def func3(...):
    ...

start([func1, func2, func3])
```

Parsing is done by treating the first argument as a command and then
passing the remaining arguments to the function associated with that
command.
```bash
~ ❯ python program.py func1 <arguments to func1>
```

See example [here](/#multiple-command) or in
[calc.py](https://github.com/oir/startle/blob/main/examples/calc.py).

You can rename commands by passing in a `dict[str, Callable]` instead of a
`list[Callable]`:

```python
start({
    "foo": func1,
    "bar": func2,
    "baz": func3,
})
```
```bash
~ ❯ python program.py baz <arguments to func3>
```