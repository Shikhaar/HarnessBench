package apierr

import "fmt"

// BUG: Simple string error without Unwrap or sentinel variables
type ApiError struct {
	Code    int
	Message string
}

func (e *ApiError) Error() string {
	return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}
