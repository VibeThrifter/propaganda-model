"""auth.py — wachtwoord- en token-hashing voor users (verbeterplan M0.6).

Alleen stdlib. Twee mechanismen, twee doelen:

- **Wachtwoorden (mensen, inlogportal):** scrypt met per-gebruiker salt waar de
  Python-build dat ondersteunt; valt terug op PBKDF2-SHA256 (600k iteraties,
  OWASP-norm) op builds zonder scrypt (macOS-systeem-Python is tegen LibreSSL
  gecompileerd en mist ``hashlib.scrypt``). Het opslagformaat draagt het schema
  (``scrypt$…`` of ``pbkdf2$…``), dus verificatie werkt altijd, ongeacht waar
  de hash ooit is gezet.
- **API-tokens (mensen én agents, Bearer):** het token is een eenmalig getoonde
  willekeurige string (``pm_…``); in de database staat alleen de sha256-hash.
  sha256 zonder salt is hier voldoende: tokens hebben 256 bits entropie en zijn
  dus niet te brute-forcen zoals wachtwoorden.

Gedeeld door server.py en scripts/create_user.py.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets

# scrypt-parameters (n=2^14 is de gangbare interactieve-login-keuze)
_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_PBKDF2_ITERATIES = 600_000

HEEFT_SCRYPT = hasattr(hashlib, "scrypt")
TOKEN_PREFIX = "pm_"


def _digest(schema: str, wachtwoord: str, salt: bytes) -> bytes:
    if schema == "scrypt":
        return hashlib.scrypt(wachtwoord.encode("utf-8"), salt=salt,
                              n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    if schema == "pbkdf2":
        return hashlib.pbkdf2_hmac("sha256", wachtwoord.encode("utf-8"), salt,
                                   _PBKDF2_ITERATIES)
    raise ValueError(f"onbekend hash-schema: {schema}")


def hash_password(wachtwoord: str) -> str:
    schema = "scrypt" if HEEFT_SCRYPT else "pbkdf2"
    salt = os.urandom(16)
    return f"{schema}${salt.hex()}${_digest(schema, wachtwoord, salt).hex()}"


def verify_password(wachtwoord: str, opgeslagen: str | None) -> bool:
    if not opgeslagen:
        return False
    try:
        schema, salt_hex, hash_hex = opgeslagen.split("$")
        digest = _digest(schema, wachtwoord, bytes.fromhex(salt_hex))
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def new_token() -> str:
    """Genereer een API-token. Wordt één keer getoond en nooit opgeslagen."""
    return TOKEN_PREFIX + secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
