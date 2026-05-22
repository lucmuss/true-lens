# Distributed Architecture

## Topology target
- 3 nodes total:
  - 1 active coordinator
  - 1 backup coordinator
  - 1 replica

## Capabilities
- Coordinator handles write orchestration.
- Replica nodes store encrypted payload copies.
- Heartbeat-based failover election if coordinator unavailable for configured period (default 1h).

## Important feasibility note
"Replica host cannot read data" is only partially achievable:
- If host fully controls runtime, plaintext can be extracted at runtime.
- Practical compromise implemented here:
  - field-level encryption at app layer for sensitive candidate fields,
  - encryption keys managed via coordinator-controlled secret scope,
  - replica stores ciphertext and metadata only.

## Data duplication policy
- Maximum replication factor configurable (default 3).
- Writes acknowledged after quorum (2/3) in strict mode or async mode by env.

## Supporter node onboarding
- Node registration request -> moderation queue -> admin approval.
- Approved node receives scoped credentials and bootstrap token.

## Internal transport security
- Signed message envelope + timestamp + nonce.
- TLS required between nodes.
- Replay protection with nonce cache.
