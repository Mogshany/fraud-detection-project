"""
gateway/fpe.py
==============
FinFlag · Format-Preserving Encryption (FPE) Module
Author: Sharon — Cryptographic Gateway Engineer

Implements FF1 (NIST SP 800-38G) with AES-256.
Designed for Kenyan M-Pesa numbers and National IDs.

Key design constraint:
  Ciphertext must be FORMAT-IDENTICAL to the plaintext:
    0722123456  →  0722891043   (10 digits, same length)
    12345678    →  71878853     (8 digits, same length)

This allows encrypted data to pass through systems that validate
phone/ID formats without revealing the real identity.

Bug fix v1.1: separate _ff1_encrypt / _ff1_decrypt with correct
Feistel swap directions per NIST SP 800-38G Algorithm 10.
"""

import math
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

RADIX  = 10   # decimal digits
ROUNDS = 10   # fixed by the FF1 spec


# ── Low-level primitives ────────────────────────────────────────────────────

def _aes_ecb(key: bytes, block: bytes) -> bytes:
    c = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    e = c.encryptor()
    return e.update(block) + e.finalize()


def _prf(key: bytes, x: bytes) -> bytes:
    """AES-CBC-MAC (zero IV) — the FF1 pseudorandom function."""
    assert len(x) % 16 == 0
    r = bytes(16)
    for i in range(0, len(x), 16):
        r = _aes_ecb(key, bytes(a ^ b for a, b in zip(r, x[i:i+16])))
    return r


def _num(s: str) -> int:
    n = 0
    for ch in s:
        n = n * RADIX + int(ch)
    return n


def _str(n: int, m: int) -> str:
    digits = []
    for _ in range(m):
        digits.append(n % RADIX)
        n //= RADIX
    return "".join(str(d) for d in reversed(digits))


def _header(n: int, u: int, t: int) -> bytes:
    """Static P block — NIST SP 800-38G Table 4."""
    return bytes([
        0x01, 0x02, 0x01,
        0x00, 0x00, RADIX,
        0x0A,
        u % 256,
        (n >> 24) & 0xFF, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF,
        (t >> 24) & 0xFF, (t >> 16) & 0xFF, (t >> 8) & 0xFF, t & 0xFF,
    ])


def _keystream(key: bytes, P: bytes, tweak: bytes,
               half: str, ri: int, b_len: int, m: int) -> int:
    """
    Derive the numeric keystream y for one Feistel round.
    'half' is the half fed into Q (B during encrypt, A during decrypt).
    """
    b_bytes = _num(half).to_bytes(b_len, "big")
    Q = tweak + bytes((-len(tweak) - b_len - 1) % 16) + bytes([ri]) + b_bytes
    rem = len(Q) % 16
    if rem:
        Q += bytes(16 - rem)

    R = _prf(key, P + Q)

    s_needed = math.ceil(math.ceil(m * math.log2(RADIX)) / 8)
    S, j = R, 1
    while len(S) < s_needed:
        S += _aes_ecb(key, bytes(a ^ b for a, b in zip(R, j.to_bytes(16, "big"))))
        j += 1
    return int.from_bytes(S[:s_needed], "big")


# ── Core FF1 (NIST SP 800-38G §6.2, Algorithm 10) ──────────────────────────

def _ff1_encrypt(key: bytes, tweak: bytes, x: str) -> str:
    """
    Encrypt x with FF1.

    NIST encrypt round:
        y  = keystream(B)
        C  = STR( (NUM(A) + y) mod radix^m, m )
        A, B = B, C          ← A becomes old-B; B becomes new-C
    """
    n = len(x)
    u = math.ceil(n / 2)
    v = n - u
    b_len = math.ceil(math.ceil(v * math.log2(RADIX)) / 8)
    P = _header(n, u, len(tweak))
    A, B = x[:u], x[u:]

    for i in range(ROUNDS):
        m = u if i % 2 == 0 else v
        y = _keystream(key, P, tweak, B, i, b_len, m)
        C = _str((_num(A) + y) % (RADIX ** m), m)
        A, B = B, C

    return A + B


def _ff1_decrypt(key: bytes, tweak: bytes, x: str) -> str:
    """
    Decrypt x with FF1.

    NIST decrypt round (rounds processed 9 → 0):
        y  = keystream(A)       ← A, not B (roles reversed vs. encrypt)
        C  = STR( (NUM(B) - y) mod radix^m, m )
        B, A = A, C             ← reverse swap
    """
    n = len(x)
    u = math.ceil(n / 2)
    v = n - u
    b_len = math.ceil(math.ceil(v * math.log2(RADIX)) / 8)
    P = _header(n, u, len(tweak))
    A, B = x[:u], x[u:]

    for i in range(ROUNDS - 1, -1, -1):
        m = u if i % 2 == 0 else v
        y = _keystream(key, P, tweak, A, i, b_len, m)   # ← A feeds Q
        C = _str((_num(B) - y) % (RADIX ** m), m)
        B, A = A, C                                      # ← reverse swap

    return A + B


# ── Public cipher class ─────────────────────────────────────────────────────

class FPECipher:
    """
    Format-Preserving Encryption for FinFlag PII fields.

    Parameters
    ----------
    key : 16, 24, or 32 bytes (AES-128/192/256)

    Example
    -------
    >>> cipher = FPECipher(os.urandom(32))
    >>> enc = cipher.encrypt_phone_prefix_safe("0722123456", tweak=b"tx-001")
    >>> dec = cipher.decrypt_phone_prefix_safe(enc, tweak=b"tx-001")
    >>> assert dec == "0722123456"
    """

    def __init__(self, key: bytes):
        if len(key) not in (16, 24, 32):
            raise ValueError("AES key must be 16, 24, or 32 bytes.")
        self._key = key

    # ── Full phone (all 10 digits scrambled) ─────────────────────────────

    def encrypt_phone(self, phone: str, tweak: bytes = b"finflag-mpesa") -> str:
        self._chk_phone_raw(phone)
        return _ff1_encrypt(self._key, tweak, phone)

    def decrypt_phone(self, masked: str, tweak: bytes = b"finflag-mpesa") -> str:
        if not masked.isdigit() or len(masked) != 10:
            raise ValueError(f"Expected 10 digits, got '{masked}'")
        return _ff1_decrypt(self._key, tweak, masked)

    # ── Prefix-safe (keeps '0722', scrambles last 6 digits) ─────────────

    def encrypt_phone_prefix_safe(self, phone: str,
                                  tweak: bytes = b"finflag-mpesa") -> str:
        """
        Encrypt the trailing 6 digits, preserving the 4-digit operator prefix.

        0722 [123456]  →  0722 [891043]
        ^^^^                   ↑ encrypted part
        """
        self._chk_phone_raw(phone)
        return phone[:4] + _ff1_encrypt(self._key, tweak, phone[4:])

    def decrypt_phone_prefix_safe(self, masked: str,
                                  tweak: bytes = b"finflag-mpesa") -> str:
        if not masked.isdigit() or len(masked) != 10:
            raise ValueError(f"Expected 10 digits, got '{masked}'")
        return masked[:4] + _ff1_decrypt(self._key, tweak, masked[4:])

    # ── National ID (6–8 digits) ─────────────────────────────────────────

    def encrypt_national_id(self, nid: str,
                             tweak: bytes = b"finflag-nid") -> str:
        self._chk_nid(nid)
        return _ff1_encrypt(self._key, tweak, nid)

    def decrypt_national_id(self, masked: str,
                             tweak: bytes = b"finflag-nid") -> str:
        if not masked.isdigit() or not (6 <= len(masked) <= 8):
            raise ValueError(f"Expected 6–8 digits, got '{masked}'")
        return _ff1_decrypt(self._key, tweak, masked)

    # ── Validators ───────────────────────────────────────────────────────

    @staticmethod
    def _chk_phone_raw(p: str):
        if not p.isdigit() or len(p) != 10:
            raise ValueError(f"Phone must be 10 digits. Got: '{p}'")
        if not (p.startswith("07") or p.startswith("01")):
            raise ValueError(f"Kenyan phone must start with 07 or 01. Got: '{p}'")

    @staticmethod
    def _chk_nid(n: str):
        if not n.isdigit() or not (6 <= len(n) <= 8):
            raise ValueError(f"National ID must be 6–8 digits. Got: '{n}'")


# ── Self-test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    key    = os.urandom(32)
    cipher = FPECipher(key)
    tweak  = b"test-session-01"

    print("=" * 58)
    print("  FinFlag FPE Self-Test")
    print("=" * 58)

    for phone in ["0722123456", "0733999888", "0101234567"]:
        enc = cipher.encrypt_phone(phone, tweak)
        dec = cipher.decrypt_phone(enc, tweak)
        ok  = "PASS ✓" if dec == phone else "FAIL ✗"
        print(f"  Phone {phone} → {enc} → {dec}  {ok}")

    print()
    phone = "0722123456"
    enc = cipher.encrypt_phone_prefix_safe(phone, tweak)
    dec = cipher.decrypt_phone_prefix_safe(enc, tweak)
    print(f"  Prefix-safe: {phone} → {enc}  (prefix={enc[:4]==phone[:4]}) → {dec}  {'PASS ✓' if dec==phone else 'FAIL ✗'}")

    print()
    for nid in ["123456", "1234567", "12345678"]:
        enc = cipher.encrypt_national_id(nid)
        dec = cipher.decrypt_national_id(enc)
        ok  = "PASS ✓" if dec == nid else "FAIL ✗"
        print(f"  NID {nid} → {enc} → {dec}  {ok}")

    print()
    e1 = cipher.encrypt_phone("0722123456", b"tweak-A")
    e2 = cipher.encrypt_phone("0722123456", b"tweak-B")
    print(f"  Tweak binding: {'PASS ✓' if e1 != e2 else 'FAIL ✗'}")
    print("=" * 58)
