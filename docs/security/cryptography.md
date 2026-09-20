# Cryptographic protocol

Encrypted objects use a versioned envelope:

```json
{"version":1,"algorithm":"AES-256-GCM","keyVersion":1,"nonce":"base64url","ciphertext":"base64url"}
```

Every encryption operation uses a fresh 96-bit nonce from the platform
cryptographic random source. Associated data may bind an item ID and revision
without exposing item contents. The client package contains the Web Crypto
envelope implementation and rejects unknown versions.

Argon2id calibration and the account-recovery protocol are intentionally
separate concerns and must be completed before production rollout.
