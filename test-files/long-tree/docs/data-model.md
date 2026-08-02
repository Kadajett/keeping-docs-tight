# The data model

The smallest change the ledger records is a posting. Each one carries an
account to debit, an account to credit, and an amount expressed in minor
units. An account balance is derived by summing its postings, because no
balance is stored anywhere in the schema.

Once written, a posting never changes. Corrections happen by appending a
reversal rather than by mutating or removing what is already there.

