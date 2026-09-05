import asyncio
from typing import Any, Dict, List


async def execute_batch(coros: List[Any]) -> Dict[str, List[Any]]:
    """Execute concurrent async tasks.

    BUG: Uncaught exception in one coroutine crashes the entire gather.
    """
    results = await asyncio.gather(*coros)
    return {"successes": list(results), "failures": []}
