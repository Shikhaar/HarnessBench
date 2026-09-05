import asyncio
from src.pipeline import execute_batch


def test_baseline_all_successful():
    async def runner():
        async def worker(val):
            await asyncio.sleep(0.001)
            return val * 2

        coros = [worker(1), worker(2), worker(3)]
        res = await execute_batch(coros)
        assert res["successes"] == [2, 4, 6]
        assert len(res["failures"]) == 0

    asyncio.run(runner())
