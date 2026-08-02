## Currency is minor units everywhere

The ledger stores minor units as integers. It never stores a decimal, because
a decimal cannot represent a third of a cent and rounding a stored balance
produces a ledger that does not balance. Formatting to a major unit happens at
the edge, in the renderer, and never in the database or the service layer.

