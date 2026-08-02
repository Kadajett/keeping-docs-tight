# The data model

The atomic unit of change in the ledger is a posting. Every posting names a
debit account, a credit account, and an amount in minor units. An account
balance comes from summing its postings, because the schema holds no stored
balance column anywhere.

A posting is immutable once written. Corrections happen by writing a reversing
posting, never by editing or deleting the original row.
