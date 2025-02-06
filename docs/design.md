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

## Enum parsing