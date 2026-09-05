import asyncio
from src.pipeline import execute_batch


def test_error_isolation():
    async def runner():
        async def good_worker(val):
            await asyncio.sleep(0.001)
            return f"item_{val}"

        async def bad_worker():
            await asyncio.sleep(0.001)
            raise ValueError("Network timeout")

        coros = [good_worker(1), bad_worker(), good_worker(2)]
        res = await execute_batch(coros)

        assert "item_1" in res["successes"]
        assert "item_2" in res["successes"]
        assert len(res["successes"]) == 2
        assert len(res["failures"]) == 1
        assert isinstance(res["failures"][0], ValueError)

    asyncio.run(runner())
