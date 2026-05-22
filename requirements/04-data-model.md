# Data Model

## Core entities
- `RecruiterUser`
- `RecruiterProfile`
- `Candidate`
- `CandidateContactPoint` (email/phone/social links)
- `CandidateAttributeDefinition`
- `CandidateAttributeVote`
- `CandidateViewLog`
- `LookupSession`
- `LookupAttempt`
- `CreditLedgerEntry`
- `CreditWallet`
- `CreditPurchase`
- `DataEnrichmentSubmission`
- `ModerationQueueItem`
- `NotificationPreference`
- `RecruiterContactIntent`
- `SecurityEvent`
- `IPBan`
- `NodeInstance`
- `ReplicationJob`
- `ReplicationEvent`

## Performance notes
- Integer foreign keys and enum smallints for categories/status.
- Separate ledger table for immutable financial history.
- Materialized counters on candidate for fast profile read.
- Index strategy:
  - candidate identity fields
  - normalized name tokens
  - lookup constraints (country/region/city)
  - vote uniqueness and date partitions
