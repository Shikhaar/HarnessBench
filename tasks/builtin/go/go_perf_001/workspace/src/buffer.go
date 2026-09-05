package buffer

type StreamAccumulator struct {
	// BUG: Naive slice reallocation creates excessive memory thrash
	data []byte
}

func NewStreamAccumulator() *StreamAccumulator {
	return &StreamAccumulator{
		data: make([]byte, 0),
	}
}

func (s *StreamAccumulator) Write(chunk []byte) (int, error) {
	s.data = append(s.data, chunk...)
	return len(chunk), nil
}

func (s *StreamAccumulator) Bytes() []byte {
	return s.data
}

func (s *StreamAccumulator) Reset() {
	// Re-allocates every time
	s.data = make([]byte, 0)
}
