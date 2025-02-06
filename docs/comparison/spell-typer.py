from typing import Annotated

import typer


def cast_spell(
    name: Annotated[str, typer.Argument(help="The name of the spell")] = "fireball",
    wizard: Annotated[str, typer.Option(help="The name of the wizard")] = "Merlin",
    mana: Annotated[
        int, typer.Option(help="The amount of mana to cast the spell")
    ] = 10,
):
    """
    Cast a spell.
    """

    print(f"{wizard} casts {name} using {mana} mana")


if __name__ == "__main__":
    typer.run(cast_spell)
