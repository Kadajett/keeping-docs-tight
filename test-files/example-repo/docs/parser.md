# The parser

The parser reads source files and writes an index. The index is then read by
the query layer downstream.

A token is a lexical unit that the parser emits, one per unit found. Each token
carries a kind, a byte span, and a line number, where kind is one of
identifier, literal, operator, or keyword.
