"""
ml_model/tokenizer_service.py
==============================
FinFlag · Financial Sentence Tokenizer
Author: Sharon — Cryptographic Gateway Engineer & Encoder LLM Engineer

THE CORE INNOVATION (Sharon's Independent Contribution):
  Standard NLP tokenizers split text like "Nairobi" → ["Na", "##iro", "##bi"].
  FinFlag's tokenizer treats FPE-encrypted phone numbers as ATOMIC tokens —
  it never splits "0722891043" into sub-word pieces because the encrypted
  digits have no linguistic meaning individually.

  This is "Semantic Feature Mapping": we convert cryptographic outputs into
  a structured natural-language space so the Transformer's Self-Attention
  can reason about fraud patterns without knowing the user's real identity.

Pipeline position:
  [Gateway FPE] → [Redis Queue] → [FinFlagTokenizer] → [Encoder LLM]

Produces two output formats:
  1. Financial Sentence (str)  — fed to BERT-style tokenizer
  2. Feature Vector (dict)     — fed to Structured ML (XGBoost / Yvonne's layer)
"""

from __future__ import annotations
import json
import math
import hashlib
from typing import Optional

# ── Risk thresholds (tuned for M-Pesa Kenyan transaction norms) ─────────────

AMOUNT_LOW    =    500.0    # KES — routine small transaction
AMOUNT_MED    =  5_000.0   # KES — medium, needs context
AMOUNT_HIGH   = 50_000.0   # KES — high-value, attention required
AMOUNT_WHALE  = 150_000.0  # KES — whale transaction, always scrutinized

RISK_LOW      = 0.20
RISK_MED      = 0.50
RISK_HIGH     = 0.75

KNOWN_LOCATIONS = {
    "juja", "nairobi", "cbd nairobi", "westlands", "mombasa",
    "kisumu", "nakuru", "eldoret", "thika", "ruiru", "kikuyu",
    "karen", "langata", "kasarani", "embakasi", "githurai",
}

IMSI_RISK = {
    "ACTIVE":  0.0,
    "UNKNOWN": 0.3,
    "SWAPPED": 0.7,
    "CLONED":  1.0,
}


# ── Helper: convert masked phone to a stable short label ────────────────────

def _phone_label(masked_phone: str) -> str:
    """
    Turn a masked phone into a 6-char hex fingerprint.
    Used as a readable stand-in for the full 10-digit ciphertext in sentences.

    Example: "0722891043" → "a3f8c1"
    This keeps sentences short while still being unique per masked identity.
    """
    digest = hashlib.sha256(masked_phone.encode()).hexdigest()
    return digest[:6]


def _amount_band(amount: float) -> str:
    """Bucket a KES amount into a descriptive band for the LLM sentence."""
    if amount < AMOUNT_LOW:
        return "micro"
    if amount < AMOUNT_MED:
        return "small"
    if amount < AMOUNT_HIGH:
        return "medium"
    if amount < AMOUNT_WHALE:
        return "large"
    return "whale"


def _risk_band(score: float) -> str:
    if score < RISK_LOW:
        return "low"
    if score < RISK_MED:
        return "moderate"
    if score < RISK_HIGH:
        return "high"
    return "critical"


def _location_flag(location: str) -> str:
    """Flag whether the location is a known Kenyan fintech hub."""
    loc = location.strip().lower()
    return "known" if loc in KNOWN_LOCATIONS else "remote"


# ── Main tokenizer class ────────────────────────────────────────────────────

class FinFlagTokenizer:
    """
    Converts a masked transaction packet (from Sharon's Gateway) into:

      (a) A "Financial Sentence" — structured text the Encoder LLM reads.
      (b) A "Feature Vector"    — numeric dict the Structured ML uses.

    Both representations are computed from the SAME masked packet, so neither
    the BERT model nor the XGBoost model ever sees raw PII.

    Usage
    -----
    >>> tok = FinFlagTokenizer()
    >>> packet = {...}   # masked JSON from Redis queue
    >>> result = tok.process(packet)
    >>> result["sentence"]       # → feed to BERT
    >>> result["feature_vector"] # → feed to XGBoost (Yvonne's layer)
    """

    # Sentence template — fields map to masked/derived values only
    TEMPLATE = (
        "Transaction by user [{uid}] at [{loc}] [{loc_flag}] location. "
        "Amount: {band} ({amount:.0f} KES). "
        "Device risk: {risk_band}. "
        "SIM status: {imsi}. "
        "Type: {tx_type}. "
        "Recipient: [{rcpt}]."
    )

    def process(self, packet: dict) -> dict:
        """
        Main entry point. Accepts the masked JSON packet from Redis.

        Parameters
        ----------
        packet : dict
            The MaskedTransactionPacket produced by gateway/main.py

        Returns
        -------
        dict with keys:
            sentence        : str   — financial sentence for Encoder LLM
            feature_vector  : dict  — numeric features for Structured ML
            behavioral_hash : str   — HMAC token (links transactions)
            metadata        : dict  — passthrough fields for logging
        """
        sentence       = self._build_sentence(packet)
        feature_vector = self._build_features(packet)

        return {
            "sentence":        sentence,
            "feature_vector":  feature_vector,
            "behavioral_hash": packet.get("behavioral_hash", "FF-unknown"),
            "metadata": {
                "sensor_id":        packet.get("sensor_id"),
                "timestamp":        packet.get("timestamp"),
                "transaction_type": packet.get("transaction_type"),
                "location":         packet.get("location"),
            },
        }

    def _build_sentence(self, p: dict) -> str:
        """
        Build the human-readable "Financial Sentence" for the Encoder LLM.

        Why a sentence? BERT-style models were pre-trained on natural language.
        By structuring transaction data AS natural language, we leverage the
        model's built-in understanding of words like "critical", "remote",
        "SWAPPED" — giving it semantic context beyond raw numbers.
        """
        uid      = _phone_label(p.get("masked_sender_phone", "0000000000"))
        rcpt_raw = p.get("masked_recipient_phone") or "self"
        rcpt     = _phone_label(rcpt_raw) if rcpt_raw != "self" else "self"
        location = p.get("location", "UNKNOWN")
        amount   = float(p.get("amount", 0))
        hw_risk  = float(p.get("hardware_risk", 0))
        imsi     = p.get("imsi_status", "UNKNOWN")
        tx_type  = p.get("transaction_type", "UNKNOWN")

        return self.TEMPLATE.format(
            uid      = uid,
            loc      = location,
            loc_flag = _location_flag(location),
            amount   = amount,
            band     = _amount_band(amount),
            risk_band= _risk_band(hw_risk),
            imsi     = imsi,
            tx_type  = tx_type,
            rcpt     = rcpt,
        )

    def _build_features(self, p: dict) -> dict:
        """
        Build the numeric Feature Vector for Yvonne's Structured ML layer.

        These are the "hard number" signals that XGBoost excels at. They are
        computed from the same masked packet — no PII required.
        """
        amount   = float(p.get("amount", 0))
        hw_risk  = float(p.get("hardware_risk", 0))
        imsi     = p.get("imsi_status", "UNKNOWN")
        location = p.get("location", "UNKNOWN")
        tx_type  = p.get("transaction_type", "UNKNOWN")
        typing_speed = p.get("typing_speed") or 0.0
        has_recipient = 1 if p.get("masked_recipient_phone") else 0

        return {
            # Amount features
            "amount":              amount,
            "amount_log":          math.log1p(amount),
            "amount_band_idx":     self._amount_band_idx(amount),
            "is_whale":            int(amount >= AMOUNT_WHALE),
            "is_round_number":     int(amount % 500 == 0),

            # Device / SIM features
            "hardware_risk":       hw_risk,
            "imsi_risk":           IMSI_RISK.get(imsi, 0.3),
            "sim_swapped":         int(imsi == "SWAPPED"),
            "sim_cloned":          int(imsi == "CLONED"),

            # Location features
            "location_known":      int(_location_flag(location) == "known"),

            # Behavioral features
            "typing_speed":        typing_speed,
            "has_recipient":       has_recipient,

            # Transaction type (one-hot)
            "tx_is_transfer":      int(tx_type == "TRANSFER"),
            "tx_is_withdrawal":    int(tx_type == "WITHDRAWAL"),
            "tx_is_payment":       int(tx_type == "PAYMENT"),
            "tx_is_deposit":       int(tx_type == "DEPOSIT"),
        }

    @staticmethod
    def _amount_band_idx(amount: float) -> int:
        """Ordinal encoding of amount band (0=micro … 4=whale)."""
        for i, threshold in enumerate([AMOUNT_LOW, AMOUNT_MED,
                                        AMOUNT_HIGH, AMOUNT_WHALE]):
            if amount < threshold:
                return i
        return 4


# ── Batch processor (pulls from a list of packets) ──────────────────────────

def tokenize_batch(packets: list[dict]) -> list[dict]:
    """Process a batch of masked packets. Returns a list of tokenizer results."""
    tok = FinFlagTokenizer()
    return [tok.process(p) for p in packets]


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Simulate what arrives from Member 3's Redis queue after Sharon's Gateway
    mock_packet = {
        "masked_sender_phone":    "0722891043",    # FPE-encrypted
        "masked_recipient_phone": "0733441289",    # FPE-encrypted
        "masked_national_id":     "71878853",      # FPE-encrypted
        "behavioral_hash":        "FF-4a7b2c9d3e1f8a7b",
        "sensor_id":              "JKUAT-SN-001",
        "imsi_status":            "SWAPPED",
        "hardware_risk":          0.72,
        "typing_speed":           38.5,
        "amount":                 4500.0,
        "transaction_type":       "TRANSFER",
        "location":               "Juja",
        "timestamp":              "2025-04-08T10:22:00Z",
    }

    tok    = FinFlagTokenizer()
    result = tok.process(mock_packet)

    print("=" * 68)
    print("  FinFlag Tokenizer Output")
    print("=" * 68)
    print("\n📝 Financial Sentence (→ Encoder LLM):")
    print(f"  {result['sentence']}")
    print("\n📊 Feature Vector (→ Structured ML / Yvonne's XGBoost):")
    for k, v in result["feature_vector"].items():
        print(f"  {k:<25} : {v}")
    print(f"\n🔑 Behavioral Hash : {result['behavioral_hash']}")
    print("=" * 68)
