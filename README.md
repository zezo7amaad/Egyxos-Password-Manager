# 🛡️ Egyxos - Enterprise Password Manager

A secure, local-first desktop password manager built with Python, featuring robust encryption, password strength analysis, and Have I Been Pwned (HIBP) API breach checking. Developed by **Abdelaziz Abdelmonem Mohamed**.

## 🚀 Features
- **Local AES Encryption**: Utilizes `Fernet` (symmetric encryption via PBKDF2HMAC with SHA-256 and 100k iterations) to secure your vault locally.
- **Master Password Verification**: Secure verifier implementation ensuring instant and reliable authentication checks.
- **Password Strength Meter**: Real-time evaluation of password complexity (length, uppercase, lowercase, numbers, and symbols).
- **Secure Password Generator**: Generates cryptographically secure random passwords.
- **HIBP Integration**: Checks stored passwords against known data breaches anonymously using k-anonymity (SHA-1 hash range queries) with asynchronous threading to prevent UI freezing.
- **Clipboard Auto-Clear**: Automatically clears sensitive copied data from the system clipboard after 20 seconds.
- **Dynamic Themes**: Fully supports both Light and Dark modern modes via CustomTkinter.

## Modern web foundation

The repository now also contains the first increment of the redesigned
zero-knowledge platform:

- `apps/web`: Next.js/React TypeScript vault workspace matching the EGYXOS
  dark visual language, with local filtering, item details, reveal/lock state,
  and responsive layout.
- `apps/api`: FastAPI boundary whose synchronization contract accepts only
  versioned encrypted payloads; it never receives a master password or vault
  plaintext.
- `packages/crypto`: Web Crypto AES-256-GCM envelope helpers with version and
  key metadata.
- `docker-compose.yml`, `.env.example`, and security architecture documents.

The original Python client remains the legacy migration reference. The web
foundation is intentionally not presented as production-complete until
Argon2id calibration, PostgreSQL/Alembic repositories, sessions/MFA,
IndexedDB persistence, organization authorization, and independent security
review are implemented.

## 🛠️ Tech Stack
- **Language**: Python 3.11+
- **GUI Framework**: CustomTkinter / Tkinter
- **Cryptography**: `cryptography`
- **Database**: SQLite3 (Isolated cross-platform storage in AppData)
- **Networking**: `requests` (for HIBP API integration)

## 📦 Installation & Usage
1. Clone the repository:
   ```bash
   git clone [https://github.com/Zezo7amaad/Egyxos-Password-Manager.git](https://github.com/Zezo7amaad/Egyxos-Password-Manager.git)
   cd Egyxos-Password-Manager