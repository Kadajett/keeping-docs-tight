# Postings

A posting is the atomic unit of change in the ledger. Every posting names a
debit account, a credit account, and an amount in minor units. Summing all
postings against an account yields that account's balance, and the schema holds
no stored balance column anywhere.

Postings are immutable once written. A mistake is corrected by writing a
reversing posting, never by editing or deleting the original row.
