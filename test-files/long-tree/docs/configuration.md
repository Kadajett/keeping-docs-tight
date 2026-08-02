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

Each default was chosen by measuring the behavior it controls under load. A
lower value rejected work that would have drained. A higher value hid
backpressure from the caller. The reasoning for every one of them is written
beside the field in `src/config.rs`, in the same comment that defines it, so
the two can never disagree with each other about what the default means or
why it was picked in the first place.
