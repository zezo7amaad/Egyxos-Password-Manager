# EGYXOS security model

EGYXOS separates account authentication from vault unlocking. The API can
authenticate an account and store opaque encrypted revisions, but it does not
receive a master password, vault key, or decrypted item. Sensitive search,
password generation, breach analysis, and encryption/decryption happen in the
client after unlock.

This repository is an incremental foundation, not a security certification.
Production deployment still requires independent review, calibrated Argon2id
parameters, secure session/token storage, PostgreSQL migrations, key recovery
design, and operational hardening.

## Legacy containment

The original CustomTkinter application remains in `main.py` as a migration
reference. Its PBKDF2/Fernet format is legacy and must only be read locally
after explicit user unlock. Do not upload its database or `vault.json`; audit
history and rotate any credentials that may have been stored there.
