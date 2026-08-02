# Retry behavior

The retry package retries a failed call up to five times before giving up.

Every failure is retried, including a 4xx client error, because a client error
is often transient in practice. Set `MaxAttempts` to zero to disable retries
entirely.

Backoff is linear. The first retry waits 100ms, the second waits 200ms, the
third waits 300ms, and so on up to the fifth.

The helper to call is `retry.Run`.
