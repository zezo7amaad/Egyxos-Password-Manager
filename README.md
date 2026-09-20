# EGYXOS Password Manager

EGYXOS is evolving from a local Python desktop password manager into a
zero-knowledge, local-first password-management platform. The repository
contains the original desktop client plus the first web/API foundation for the
new architecture.

> **Security status:** The web foundation is an incremental development build,
> not a production security certification. Do not use it to store real secrets
> until the remaining authentication, persistence, synchronization, recovery,
> and independent security-review work is complete.

## Repository areas

| Path | Purpose |
| --- | --- |
| `main.py` | Legacy CustomTkinter desktop client and migration reference |
| `apps/web` | Next.js, React, and TypeScript vault workspace |
| `apps/api` | FastAPI API boundary for account and encrypted sync operations |
| `packages/crypto` | Versioned Web Crypto AES-256-GCM envelope helpers |
| `tools/migrate_legacy_egyxos.py` | Safe, inspection-only legacy SQLite report |
| `docs/security` | Architecture, cryptography, and threat-model documentation |
| `docker-compose.yml` | Local web, API, PostgreSQL, and Redis topology |

## Current web foundation

The web workspace follows the supplied EGYXOS design language:

- Near-black premium interface with thin borders and rounded panels
- EGYXOS branding and official logo
- Sidebar navigation for Home, Vault, Favorites, Generator, Security Center,
  and Settings
- Vault categories, local search, item list, favorites, item details, copy
  actions, password reveal state, and lock overlay
- Responsive behavior for smaller screens

The API accepts opaque encrypted payloads only. It does not receive a master
password, decrypted vault key, or plaintext vault item. Account registration
and login use Argon2id verifiers and randomly generated, database-backed
opaque session tokens (only token hashes are persisted). PostgreSQL stores
encrypted vault revisions and rejects stale or out-of-order mutations with a
revision conflict response.

## Legacy desktop client

The original client provides:

- Local SQLite vault storage under the user application-data directory
- Fernet encryption with PBKDF2-HMAC-SHA256
- Password strength analysis and cryptographically secure generation
- HIBP k-anonymity breach checks
- Clipboard auto-clear
- Light and dark CustomTkinter themes

The legacy encryption format is retained for compatibility and migration
reference only. It is not the target protocol for the web platform. Do not
commit real vault databases, exports, or credentials.

## Development

### Web application

Requirements: Node.js 20 or newer.

```bash
npm install
npm run dev:web
```

The web application runs at `http://localhost:3000`.

Useful checks:

```bash
npm run typecheck
npm run build:web
```

### API

Requirements: Python 3.11+ for local development. The container uses Python
3.12.

```bash
python -m pip install -r apps/api/requirements.txt
$env:PYTHONPATH = "."
python -m uvicorn apps.api.app.main:app --reload --port 8000
```

The API runs at `http://localhost:8000`. OpenAPI documentation is available
at `/docs` while the development server is running.

### Docker Compose

Copy `.env.example` to `.env`, replace development placeholders, then run:

```bash
docker compose up --build
```

The development services use ports 3000 (web), 8000 (API), 5432
(PostgreSQL), and 6379 (Redis).

## Legacy vault inspection

The migration helper reports tables, columns, and record counts without
decrypting or printing secrets:

```bash
python tools/migrate_legacy_egyxos.py path\to\egyxos_vault.db
```

Full migration must remain a local, user-authorized workflow. Plaintext
records must be re-encrypted into the new versioned client-side format before
any encrypted payload is uploaded.

## Zero-knowledge design

The intended trust boundary is:

1. Account authentication is handled separately from vault unlocking.
2. The client derives or unwraps vault keys locally after unlock.
3. Vault data is encrypted client-side using versioned authenticated encryption.
4. Search, password generation, and breach analysis operate locally.
5. The server stores and synchronizes opaque encrypted revisions and metadata.
6. Organization authorization and audit metadata are enforced server-side,
   while shared collection contents remain encrypted.

The current envelope format is documented in
[`docs/security/cryptography.md`](docs/security/cryptography.md). The broader
security model and limitations are documented in
[`SECURITY.md`](SECURITY.md).

## Roadmap

The remaining implementation is intentionally staged:

1. Add Argon2id calibration and client-side key hierarchy.
2. Add email verification, MFA, rate limiting, and device revocation.
3. Add IndexedDB encrypted local persistence, offline mutation queues, and
   incremental synchronization.
5. Add vault item CRUD for logins, cards, identities, and secure notes.
6. Add organizations, collections, RBAC, encrypted sharing, and audit logs.
7. Add migration re-encryption, automated security tests, monitoring,
   encrypted backups, and production deployment controls.

## Security reporting

Please do not disclose suspected vulnerabilities in public issues. Review
[`SECURITY.md`](SECURITY.md) for the current security model and report
security-sensitive findings privately to the repository maintainer.
