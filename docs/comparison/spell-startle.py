from startle import start


def cast_spell(
    name: str = "fireball",
    /,
    *,
    wizard: str = "Merlin",
    mana: int = 10,
):
    """
    Cast a spell.

    Args:
        name: The name of the spell
        wizard: The name of the wizard
        mana: The amount of mana to cast the spell
    """

    print(f"{wizard} casts {name} using {mana} mana")


if __name__ == "__main__":
    start(cast_spell)
