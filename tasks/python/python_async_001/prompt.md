# Async Concurrency: Batch Pipeline Error Isolation

### Context
In `src/pipeline.py`, `execute_batch()` dispatches concurrent asynchronous operations using standard `asyncio.gather(*tasks)`. A single failure abruptly aborts the entire gather call, discarding results of successfully completed concurrent tasks.

### Objective
1. Update `execute_batch(coros: list)` in `src/pipeline.py` using `asyncio.gather(*coros, return_exceptions=True)`.
2. Partition the results into two distinct lists:
   - `successes`: values that completed without exceptions
   - `failures`: exception instances encountered
3. Return a dictionary `{"successes": successes, "failures": failures}`.

### Style
Modern asynchronous Python 3 with clean list partitioning.

### Tone
Technical, concurrent-systems focused.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Modify `src/pipeline.py` to isolate coroutine failures without leaving lingering unawaited tasks.
