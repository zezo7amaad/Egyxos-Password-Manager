# Threat model

The design protects vault contents from a compromised synchronization database,
database backups, API operators, and network observers. It does not protect
plaintext while a device is unlocked, a compromised browser/runtime, malicious
browser extensions, or a stolen unlocked session.

Important controls are local-only search, opaque API contracts, authenticated
encryption, per-device sessions, authorization checks, rate limiting, secure
cookies, CSP, dependency scanning, and verified encrypted backups.
