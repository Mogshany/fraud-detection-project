"""
gateway/hashing.py
==================
FinFlag · Privacy-Preserving Identity Linking
Author: Sharon — Cryptographic Gateway Engineer

Salted HMAC-SHA256 produces a stable "behavioral token" per identity.
The AI can group transactions by the same token without ever seeing the
real phone number, name, or National ID.

Token properties:
  • Deterministic  — same input + same salt → same token (linkable across time)
  • Non-reversible — HMAC cannot be inverted without the secret salt
  • Compartmented  — rotating the salt produces a completely different token set
  • Timing-safe    — verify() uses hmac.compare_digest to resist timing attacks
"""

import hmac
import hashlib
import os
import base64

PREFIX = "FF-"   # visual marker for FinFlag tokens in logs


def _hmac256(secret: bytes, message: str) -> str:
    return hmac.new(secret, message.encode("utf-8"), hashlib.sha256).hexdigest()


class IdentityHasher:
    """
    Generates stable behavioral tokens from PII fields.

    The SALT must:
      1. Be generated once at system startup and stored in a secret vault.
      2. NEVER be stored alongside the hashed data.
      3. Be rotated periodically for compartmentalization.

    Example
    -------
    >>> hasher = IdentityHasher(salt=os.urandom(32))
    >>> token  = hasher.hash_phone("0722123456")
    >>> hasher.verify_phone("0722123456", token)
    True
    """

    def __init__(self, salt: bytes):
        if len(salt) < 16:
            raise ValueError("Salt must be at least 16 bytes.")
        self._salt = salt

    # ── Phone ────────────────────────────────────────────────────────────

    def hash_phone(self, phone: str, context: str = "mpesa") -> str:
        """
        Produce a behavioral token for an M-Pesa number.

        The context namespace prevents a phone '0722123456' and an NID
        that happens to read '0722123456' from producing the same token.
        """
        self._chk_phone(phone)
        return PREFIX + _hmac256(self._salt, f"{context}:{phone}")[:32]

    def verify_phone(self, phone: str, token: str,
                     context: str = "mpesa") -> bool:
        return hmac.compare_digest(self.hash_phone(phone, context), token)

    # ── National ID ──────────────────────────────────────────────────────

    def hash_national_id(self, nid: str) -> str:
        self._chk_nid(nid)
        return PREFIX + _hmac256(self._salt, f"nid:{nid}")[:32]

    def verify_national_id(self, nid: str, token: str) -> bool:
        return hmac.compare_digest(self.hash_national_id(nid), token)

    # ── Name (audit log only — not sent to AI) ───────────────────────────

    def hash_name(self, full_name: str) -> str:
        normalized = full_name.strip().lower()
        return PREFIX + _hmac256(self._salt, f"name:{normalized}")[:32]

    # ── Composite identity (phone + ID together) ─────────────────────────

    def hash_composite_identity(self, phone: str, nid: str) -> str:
        """
        Token that represents the *combination* of phone + ID.
        Two people with the same phone but different IDs get different tokens.
        """
        self._chk_phone(phone)
        self._chk_nid(nid)
        return PREFIX + _hmac256(self._salt, f"composite:{phone}:{nid}")[:32]

    # ── Salt helpers ──────────────────────────────────────────────────────

    @staticmethod
    def generate_salt(nbytes: int = 32) -> bytes:
        """Generate a cryptographically secure random salt."""
        return os.urandom(nbytes)

    @staticmethod
    def to_env(salt: bytes) -> str:
        """Encode salt as a base64 string for storage in an env variable."""
        return base64.b64encode(salt).decode("ascii")

    @staticmethod
    def from_env(env_val: str) -> bytes:
        """Decode a base64 env variable back to raw bytes."""
        return base64.b64decode(env_val.encode("ascii"))

    # ── Validators ────────────────────────────────────────────────────────

    @staticmethod
    def _chk_phone(p: str):
        if not p.isdigit() or len(p) != 10:
            raise ValueError(f"Phone must be 10 digits. Got: '{p}'")

    @staticmethod
    def _chk_nid(n: str):
        if not n.isdigit() or not (6 <= len(n) <= 8):
            raise ValueError(f"National ID must be 6–8 digits. Got: '{n}'")


def hasher_from_env(env_var: str = "FINFLAG_HMAC_SALT") -> IdentityHasher:
    """Load salt from an environment variable and return a ready hasher."""
    raw = os.environ.get(env_var)
    if not raw:
        raise RuntimeError(
            f"'{env_var}' is not set. Generate it with:\n"
            "  python -c \"import os,base64; print(base64.b64encode(os.urandom(32)).decode())\""
        )
    return IdentityHasher(IdentityHasher.from_env(raw))


if __name__ == "__main__":
    print("=" * 50)
    print("  FinFlag HMAC Identity Hasher Self-Test")
    print("=" * 50)
    salt   = IdentityHasher.generate_salt()
    hasher = IdentityHasher(salt)

    t1 = hasher.hash_phone("0722123456")
    t2 = hasher.hash_phone("0722123456")
    t3 = hasher.hash_phone("0733999888")

    print(f"\n  Token A : {t1}")
    print(f"  Token A': {t2}")
    print(f"  Deterministic  : {'PASS ✓' if t1 == t2 else 'FAIL ✗'}")
    print(f"  A ≠ B          : {'PASS ✓' if t1 != t3 else 'FAIL ✗'}")
    print(f"  Verify correct : {'PASS ✓' if hasher.verify_phone('0722123456', t1) else 'FAIL ✗'}")
    print(f"  Verify wrong   : {'PASS ✓' if not hasher.verify_phone('0733999888', t1) else 'FAIL ✗'}")

    t_nid  = hasher.hash_national_id("12345678")
    t_comp = hasher.hash_composite_identity("0722123456", "12345678")
    print(f"\n  NID token       : {t_nid}")
    print(f"  Composite token : {t_comp}")
    print(f"  Cross-field iso : {'PASS ✓' if t1 != t_nid else 'FAIL ✗'}")
    print(f"  Composite unique: {'PASS ✓' if t_comp != t1 and t_comp != t_nid else 'FAIL ✗'}")

    new_hasher = IdentityHasher(IdentityHasher.generate_salt())
    t_new = new_hasher.hash_phone("0722123456")
    print(f"\n  Salt rotation   : {'PASS ✓' if t_new != t1 else 'FAIL ✗'}")
    print("=" * 50)
