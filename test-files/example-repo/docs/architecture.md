# Architecture

The parser reads source files and writes an index. The index is read by the
query layer. See `src/parser.go` for the parser, whose module comment is the
contract for what a token is.

A token is a lexical unit. The parser emits one token per lexical unit it
finds. Tokens carry a kind, a byte span, and a line number. The kind is one of
identifier, literal, operator, or keyword. The byte span is a half-open range
into the source. The line number is one-based. All of this is restated in the
module comment on `src/parser.go`, which is authoritative.
