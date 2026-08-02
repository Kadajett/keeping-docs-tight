# Changelog

## v2.4.0

We're excited to announce three significant improvements to the retry
subsystem. The good news is that all of them are backwards compatible.

First, we've dramatically improved retry performance. It's not just faster,
it's more predictable. Rather than using a fixed backoff, the scheduler now
uses an exponential one, which may improve tail latency somewhat under load.

Second, you did not previously have a way to cap total retry duration. We've
added one. The new `max_total_retry` setting lives in the retry section of your
config.

Finally, it's worth noting that the dead-letter queue is now durable, robust,
and observable. Ultimately, this means fewer lost widgets.
