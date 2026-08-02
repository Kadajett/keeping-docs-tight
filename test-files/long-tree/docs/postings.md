# Postings

A posting is the atomic unit of change in the ledger. Every posting names a
debit account, a credit account, and an amount in minor units. The sum of all
postings against any account is that account's balance, and the ledger holds
no stored balance column at all.

Postings are immutable once written. A mistake is corrected by writing a
reversing posting, never by editing or deleting the original row.

