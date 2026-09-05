# Go Performance: Optimize Stream Accumulator Buffer Reallocation

### Context
In `src/buffer.go`, `StreamAccumulator` accumulates byte chunks. It currently allocates fresh slices on every `Reset()` call and appends chunks naively, causing heavy GC pressure and heap fragmentation.

### Objective
1. Refactor `StreamAccumulator` in `src/buffer.go` to use `bytes.Buffer`.
2. Implement `Write(chunk []byte) (int, error)` streaming directly into the buffer.
3. Implement `Bytes() []byte` returning `b.buf.Bytes()`.
4. Implement `Reset()` invoking `b.buf.Reset()` to clear contents without discarding underlying allocated capacity.

### Style
Idiomatic Go memory-efficient I/O patterns.

### Tone
Performance-oriented, memory-allocation sensitive.

### Audience
Autonomous AI coding agent runtime operating inside an isolated workspace.

### Response
Modify `src/buffer.go` to minimize heap allocations and maximize throughput.
