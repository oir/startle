"""
Shows `start()` consuming an `async def` function, and running it
using asyncio.run.

Example invocations:
    python examples/parallel_wait.py greet welcome host say-hi
"""

import asyncio
import time

from startle import start


async def parallel_wait(tasks: list[str], *, duration: float = 1.0) -> None:
    """
    Pretend to run several tasks in parallel, each taking `duration` seconds.

    Args:
        tasks: Names of the tasks to run.
        duration: Seconds each task takes.
    """

    async def run(name: str) -> None:
        await asyncio.sleep(duration)
        print(f"finished {name}")

    t0 = time.monotonic()
    await asyncio.gather(*(run(t) for t in tasks))
    elapsed = time.monotonic() - t0
    print(
        f"ran {len(tasks)} tasks in {elapsed:.2f}s "
        f"(serial would take {len(tasks) * duration:.2f}s)"
    )


start(parallel_wait)
