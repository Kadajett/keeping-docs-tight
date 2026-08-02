# Configuration

Every setting is defined in `src/config.rs`, which is the authoritative source
and carries a comment on each field explaining its default.

| Setting | Default | Controls |
|---|---|---|
| `field_1` | 7 | behavior 1 |
| `field_2` | 14 | behavior 2 |
| `field_3` | 21 | behavior 3 |
| `field_4` | 28 | behavior 4 |
| `field_5` | 35 | behavior 5 |
| `field_6` | 42 | behavior 6 |
| `field_7` | 49 | behavior 7 |
| `field_8` | 56 | behavior 8 |
| `field_9` | 63 | behavior 9 |
| `field_10` | 70 | behavior 10 |
| `field_11` | 77 | behavior 11 |
| `field_12` | 84 | behavior 12 |

The `workers` default is the CPU core count, because spawning more workers than
cores produces contention without throughput. The `queue_depth` default is one
thousand: a deeper queue hides backpressure from the caller, and a shallower one
rejects bursts that would have drained on their own. The `timeout` default is
thirty seconds, long enough for the slowest observed request and short enough
that a stuck one does not hold a worker for a whole shift. The `retries` default
is three, because most transient failures resolve by the second attempt and a
fourth has never changed an outcome in the recorded history.

The `log_level` default is info, which prints one line per request and nothing
per retry, so an operator reading the log sees work rather than noise. The
`flush_interval` default is five seconds, chosen so a crash loses at most one
window of buffered rows. The `shard_count` default is sixteen, which divides
evenly across every deployment size in use and leaves headroom to double
without a rebalance.
