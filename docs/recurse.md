# Recursive parsing

_`recurse=True` is experimental, consider its API as unstable and evolving._

Sometimes a config class nests other config classes.
Setting `recurse=True` on either `start()` or `parse()` makes
**Startle** to recursively walk _into_ such nested attributes,
expose their individual fields as CLI options, and then recursively
construct children and parent instances at program invocation time.

For example:

<div class="code-file" style="--filename:'digits.py'">

```python
@dataclass
class RandomForestConfig:
    """
    Configuration for the RandomForestClassifier.

    Attributes:
        n_estimators: The number of trees in the forest.
        criterion: The function to measure the quality of a split.
        max_depth: The maximum depth of the tree.
    """

    n_estimators: int = 100
    criterion: Literal["gini", "entropy"] = "gini"
    max_depth: int | None = None


@dataclass
class DatasetConfig:
    """
    Configuration for the dataset split.

    Attributes:
        test_size: The proportion of the dataset to include in the test split.
        shuffle: Whether or not to shuffle the data before splitting.
    """

    test_size: float = 0.5
    shuffle: bool = True


def fit_rf(
    model_config: RandomForestConfig,
    dataset_config: DatasetConfig,
    *,
    quiet: bool = False,
    output_file: Path | None = None,
):
    """
    Fit a RandomForestClassifier on the digits dataset and
    print the classification report.

    Args:
        model_config: Configuration for the RandomForestClassifier.
        dataset_config: Configuration for the dataset split.
        quiet: If True, suppress output.
        output_file: Optional path to save the output.
    """

    ...


if __name__ == "__main__":
    start(fit_rf, recurse=True)
```

</div>

<div id="digits-help-cast"></div>

See full example at 
[digits.py](https://github.com/oir/startle/blob/main/examples/digits.py).

## Nested types

A field becomes a _nested type_ (gets walked into) when its annotation is one
of:

- a `@dataclass` class,
- a regular class with `__init__`,
- a `TypedDict` subclass.

These are the same three kinds of types that `parse()` can admit.
Anything else is a _leaf_: primitives, enums, `typing.Literal`,
`Optional` of a scalar, n-ary containers (`list[T]`, `set[T]`, ...), and any
user defined types registered with `register()`.

## Flat vs nested naming

`recurse=True` has two naming modes, controlled by `naming="flat"` (default)
or `naming="nested"`. Consider:

```python
from dataclasses import dataclass, field
from startle import start


@dataclass
class DBConfig:
    """
    Attributes:
        host: Database hostname.
        port: Database port.
    """

    host: str = "localhost"
    port: int = 5432


@dataclass
class ServerConfig:
    """
    Attributes:
        db: Database configuration.
        workers: Number of workers.
    """

    db: DBConfig = field(default_factory=DBConfig)
    workers: int = 4


def serve(server: ServerConfig) -> None:
    """Run a server."""


start(serve, recurse=True)  # naming="flat" by default
```

Under `naming="flat"`, leaves are exposed at the top level with their bare
names:

<div id="recurse-help-flat-cast"></div>

Under `naming="nested"`, each leaf carries the dotted path of its nesting:

<div id="recurse-help-nested-cast"></div>

Considerations:

- **Flat** is shorter to type and auto-assigns short names to leaves
  (`-h`, `-p`, `-w` above). But because the names are collapsed, every leaf
  in the tree must have a unique name, or a `NameCollisionError` will be
  raised.
- **Nested** is self-disambiguating: You can have two different subtrees
  that both contain a `port` field without conflict. Short names on leaves
  are not auto-assigned in this mode (the dotted path is already explicit,
  and leaf short letters would collide constantly across subtrees).

## Optional nested types and partial input

The most subtle part of recursive parsing is what happens when a nested type
has a default. **Startle** follows a "user intent" rule: If you
touched _any_ leaf inside an optional nested type, the whole thing is
instantiated (and required leaves that are not provided raise an error);
if you touched _nothing_ inside it, the default is preserved.

Consider:

```python
@dataclass
class DBConfig:
    host: str            # required
    port: int = 5432


@dataclass
class ServerConfig:
    db: DBConfig | None = None
    workers: int = 4


def main(server: ServerConfig) -> None: ...


start(main, recurse=True)
```

Example invocations:

| CLI input | `server.db` | `server.workers` |
| --- | --- | --- |
| (nothing) | `None` | `4` |
| `--workers 8` | `None` | `8` |
| `--host example.com` | `DBConfig(host="example.com", port=5432)` | `4` |
| `--port 6000` | Error: `host` is required | — |
| `--host db.co --port 6000` | `DBConfig(host="db.co", port=6000)` | `4` |

## Limitations

Several cases of configurations are not allowed, and will raise a
`ParserConfigError`-derived error at parser construction time:

- `recurse=True` with a list or dict of functions (subcommand dispatch)
  raises `CmdsRecurseError`. Recursive parsing is currently supported
  only with a single function or class.
- Variadic `*args` / `**kwargs` on a _nested_ type raises
  `VariadicChildParamError`. Top-level variadics on the entry function
  still work.
- Recursing into an n-ary container like `list[Cfg]` raises
  `NaryNonRecursableParamError`, _nested_ types cannot be n-ary.
- Recursive type cycles (e.g. a dataclass that transitively references
  itself) raise `RecursiveTypeError`.


<script>
AsciinemaPlayer.create('cast/digits-help.cast', document.getElementById('digits-help-cast'), {
    autoPlay: true,
    controls: true,
    speed: 2,
    rows: 22,
    terminalFontFamily: "'Fira Mono', monospace",
    terminalFontSize: "12px",
    fit: false,
    theme: "custom-auto",
});
AsciinemaPlayer.create('cast/recurse-help-flat.cast', document.getElementById('recurse-help-flat-cast'), {
    autoPlay: true,
    controls: true,
    speed: 2,
    rows: 14,
    terminalFontFamily: "'Fira Mono', monospace",
    terminalFontSize: "12px",
    fit: false,
    theme: "custom-auto",
});
AsciinemaPlayer.create('cast/recurse-help-nested.cast', document.getElementById('recurse-help-nested-cast'), {
    autoPlay: true,
    controls: true,
    speed: 2,
    rows: 14,
    terminalFontFamily: "'Fira Mono', monospace",
    terminalFontSize: "12px",
    fit: false,
    theme: "custom-auto",
});
</script>
