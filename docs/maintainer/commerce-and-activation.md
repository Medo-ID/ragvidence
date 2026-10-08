# Commerce and Plus activation design

This file is internal and excluded from customer source distributions.

PayPal processes payment; it is not the product-license authority. A small backend must connect verified payment state to a RAGvidence entitlement.

## Required flow

1. The landing-page server creates a PayPal order for a server-controlled product ID and price.
2. The buyer approves checkout.
3. The server captures the order and independently verifies the resulting order/capture details.
4. A webhook endpoint accepts payment events but fulfills only after PayPal signature verification and a completed capture.
5. The backend stores an idempotent entitlement keyed by PayPal capture/order ID and buyer identity.
6. The backend emails or displays a one-time activation code or authenticated download link.
7. `ragvi license activate CODE` exchanges that code for a signed, non-secret license document.
8. The CLI verifies the document with an embedded public key and stores it in the user configuration directory with restrictive permissions.
9. Plus feature checks read the verified entitlement. The private signing key exists only in the backend or a managed secret store.
10. Refund, chargeback, cancellation, and fraud events revoke future downloads/refreshes. Define an explicit offline grace policy before launch.

## Security requirements

- Never embed a PayPal client secret, webhook secret, signing private key, or entitlement database credential in the CLI, browser bundle, repository, release archive, or license document.
- Verify PayPal webhook signatures before changing order state.
- Treat webhook delivery as repeatable and out of order; operations must be idempotent.
- Fulfill only `COMPLETED` captures for the expected currency, amount, merchant, and server-controlled product identifier.
- Never trust a plan or price sent only by the browser.
- Bind activation to the buyer without collecting unnecessary device fingerprints.
- Store only necessary purchase and entitlement data; define deletion and retention rules.
- Rate-limit activation and webhook endpoints and keep security-relevant audit logs without API credentials or document content.
- Provide a manual recovery path for legitimate buyers.

## Recommended v1 boundary

- Free: no account and no activation.
- Plus: individual entitlement, private Plus artifact, signed offline-verifiable license, limited online refresh for revocation and updates.
- Teams: deferred until roles, seats, organization ownership, and support obligations are designed.

Do not implement runtime gating until at least one real Plus feature is complete. Selling only a promise of future Plus functionality creates avoidable customer and legal risk.
