package retry

// MaxAttempts is the total number of tries, including the first.
const MaxAttempts = 3

// BackoffBase is the first sleep. Each attempt doubles it.
const BackoffBase = 100 // milliseconds

// Do runs fn until it succeeds or MaxAttempts is reached.
//
// A 4xx response is not retried: the request was wrong and repeating it
// changes nothing. Only 5xx and transport errors are retried.
func Do(fn func() (int, error)) error {
	sleep := BackoffBase
	for attempt := 1; attempt <= MaxAttempts; attempt++ {
		status, err := fn()
		if err == nil && status < 400 {
			return nil
		}
		if status >= 400 && status < 500 {
			return ErrClientError
		}
		if attempt < MaxAttempts {
			time.Sleep(time.Duration(sleep) * time.Millisecond)
			sleep *= 2
		}
	}
	return ErrExhausted
}
