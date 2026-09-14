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