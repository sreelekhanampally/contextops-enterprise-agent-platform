# Atlas Commerce Product Manual

Atlas Commerce provides order processing, checkout, payment orchestration, and refund workflows for enterprise merchants.

## Checkout availability
The checkout API is considered critical. Persistent P95 latency above the published service objective should trigger Platform Engineering investigation. If customer transactions fail or time out at scale, the issue should be handled through the production incident process.

## Refund operations
Refund batches are processed asynchronously. Customer Support can inspect refund state but cannot alter payment-provider settlement records directly.
