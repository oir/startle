# Design

This section describes the motivation behind some of the design
decisions in **Startle**.

## Non-intrusive

**Startle** aims to provide a very narrow interface and
be **non-intrusive** to user classes and functions.

This concretely means the following:
1. Configuration and customization points should modify user functions and classes
   as little as possible.
2. If they _do_ modify, they should use native Python objects, and not
   **Startle**-specific library objects.

To illustrate with an example using Typer and Startle:

<div class="code-file" style="--filename:'spell-typer.py'">

[spell-typer.py](comparison/spell-typer.py ':include :type=code')

</div>

<div class="code-file" style="--filename:'spell-startle.py'">

[spell-startle.py](comparison/spell-startle.py ':include :type=code')

</div>

In the Typer example, because of `typer.Argument()` and `typer.Option()` objects
appearing in the signature, `cast_spell()` function now has a dependency on `typer`.
In the example below, `cast_spell()` is a pure Python function and does not have
a `startle` dependency.

This "non-intrusive" approach has the following benefits:
- `cast_spell()` can be used as a library dependency (as opposed to a CLI dependency)
  elsewhere, without introducing a `startle` dependency. For instance, CLI part of 
  your library can have an _extra_ dependency for `startle`, but the main library can
  omit it.
- Similarly, it is easier to copy paste into another library entirely with no modifications,
  or more easily used as reference.
- Makes it easier to adopt Startle in a new codebase for the first time, as well as
  _un_-adopt it later if you decide it is no longer needed.
- Since `cast_spell()` is native Python, it is easier to reason about, as it is more
  familiar to users who might not know about Startle's own data structures.


## Simple custom parser

It would be preferable to rely on the native `argparse` module for parsing by constructing
an `ArgumentParser` object from functions or classes, and merely invoking
`ArgumentParser.parse_args()`, which would have the benefit of being more familiar to
users. However `argparse` does not support arguments that are both positional and named
options. To better align with the functional interface where a function argument could be both
(if between `/` and `*`), a custom parser was needed.

To this end **Startle** has its own `Args` class with a custom, yet simple parsing logic.

This also had the benefit of more easily itegrating `rich` for prettier help strings.


## Enum parsing

Traditionally, enums are used to represent a set of options as a set of names, while possibly
hiding the actual underlying value. For example, for a suit of cards, one might have:
```py
class Suit(Enum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3
```
Then, the main motivation is to interact with, e.g. `Suit.HEARTS`, instead of the value `2`
throughout the code.

To align with this, **Startle** will expect to see `hearts` in the command line as opposed
to `2`, as _names_, rather than _values_ is considered to be the interface.
Therefore, in the general case, parser is generated based on the names of the options.

However in the special case where values are `str`s, enums may be used in a 
_value-aware_ manner, interchangeably with a string:
```py
class Suit(StrEnum):
# class Suit(str, Enum):  # alternative, prior to StrEnum availability
    CLUBS = "clubs"
    DIAMONDS = "diamonds"
    HEARTS = "hearts"
    SPADES = "spades"
```
In this case, the _value_ is considered _visible_, and part of the interface.
Thus, in the special case of string based enums, parser is generated based on the values of the options.
In this particular example, both names and values would yield the same expected command line
string, but if our enum had looked like this (for illustration purposes):
```py
class Suit(StrEnum):
# class Suit(str, Enum):  # alternative, prior to StrEnum availability
    SUIT_CLUBS = "clubs"
    SUIT_DIAMONDS = "diamonds"
    SUIT_HEARTS = "hearts"
    SUIT_SPADES = "spades"
```
then `hearts` would be expected from the command line and `suit-hearts` would be unrecognized.