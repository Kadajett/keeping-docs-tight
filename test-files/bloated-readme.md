# Widgetd

Widgetd is a daemon that manages widgets. A widget is a unit of work that the
system processes asynchronously. This README will walk you through everything
you need to know in order to get started with Widgetd, whether you're a
first-time user or an experienced operator.

## Installation

Before you can install Widgetd, you will need to make sure that you have the
prerequisites installed on your system. Widgetd requires Go 1.21 or later.
Installation is done via the standard Go toolchain, which most developers will
already be familiar with, and which handles dependency resolution for you.

```bash
go install github.com/example/widgetd@latest
```

## The configuration file

Widgetd is configured through a configuration file. The configuration file is
written in TOML, which is a configuration file format that is designed to be
easy for humans to read due to its obvious semantics. The full specification
for the configuration file format lives in `config/schema.go`, which is the
authoritative source.

The configuration file has a number of fields. The `workers` field controls how
many worker goroutines are spawned at startup. The `queue_depth` field controls
how many widgets may be buffered before backpressure is applied. The `timeout`
field controls how long a single widget may take before it is abandoned. The
`retries` field controls how many times an abandoned widget is retried. The
`log_level` field controls verbosity. Each of these fields has a default, and
the defaults are documented in `config/schema.go` alongside the field
definitions themselves, with a comment on each explaining the reasoning.

The `workers` default is the number of CPU cores reported by the runtime,
because spawning more workers than cores produces contention without
throughput. The `queue_depth` default is one thousand, chosen because a deeper
queue hides backpressure from the caller and a shallower one rejects bursts
that would have drained. The `timeout` default is thirty seconds, which is
long enough for the slowest widget observed in production and short enough that
a stuck widget does not hold a worker for a whole shift. The `retries` default
is three, because most transient failures resolve by the second attempt and a
fourth attempt has never changed an outcome in the recorded history. The
`log_level` default is info, which prints one line per widget and nothing per
retry, so an operator reading the log sees work rather than noise.

## Running it

Once you have installed Widgetd and written a configuration file, you can run
it. Running it is straightforward and requires no special privileges.

```bash
widgetd --config widgetd.toml
```

## Supported platforms

| Platform | Supported |
|---|---|
| Linux | yes |
| macOS | yes |
| Windows | no |

## Contributing

We welcome contributions. Please open an issue first to discuss what you would
like to change. Make sure to update tests as appropriate.
