# Security architecture

The web client is the trust boundary for vault plaintext. It derives a
client-side vault key, decrypts encrypted envelopes in memory, and writes only
versioned AES-256-GCM envelopes to the synchronization API. The server is an
availability, authentication, authorization, and encrypted-storage service.

Account credentials use a separate server-side verifier and must never be used
as the vault key. Organization membership and audit metadata are server-side;
shared collection contents remain encrypted and are wrapped for authorized
devices.
