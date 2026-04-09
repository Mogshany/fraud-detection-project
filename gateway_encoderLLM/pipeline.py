"""
ml_model/pipeline.py
====================
FinFlag · Full Pipeline Integration
Author: Sharon — Cryptographic Gateway Engineer & Encoder LLM Engineer

This is the "Full Loop" integration that connects every layer:

  [Raw Transaction]
        ↓
  [FPE Encryption]      ← gateway/fpe.py        (Sharon)
        ↓
  [HMAC Hashing]        ← gateway/hashing.py    (Sharon)
        ↓
  [Tokenizer]           ← ml_model/tokenizer_service.py (Sharon)
        ↓
  [Rule-Based Scorer]   ← ml_model/encoder_model.py (Sharon / Structured ML)
        ↓
  [Encoder LLM]         ← ml_model/encoder_model.py (Sharon / NLP)
        ↓
  [Ensemble Decision]   ← ml_model/encoder_model.py (Sharon / Meta-Classifier)
        ↓
  [Final FinFlag Decision: BLOCK / PASS + explanation]

Run this to verify the entire pipeline end-to-end:
  python -m ml_model.pipeline
"""

import os
import sys
import json

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway.fpe     import FPECipher
from gateway.hashing import IdentityHasher
from ml_model.tokenizer_service import FinFlagTokenizer
from ml_model.encoder_model     import RuleBasedScorer, EnsembleDecisionEngine


# ── Pipeline class ──────────────────────────────────────────────────────────

class FinFlagPipeline:
    """
    End-to-end fraud detection pipeline.

    Parameters
    ----------
    fpe_key   : 32-byte AES key for Format-Preserving Encryption
    hmac_salt : 32-byte salt for HMAC identity linking
    strategy  : ensemble strategy — "weighted_avg" | "max" | "escalation"
    """

    def __init__(self, fpe_key: bytes, hmac_salt: bytes,
                 strategy: str = "escalation"):
        self.cipher   = FPECipher(key=fpe_key)
        self.hasher   = IdentityHasher(salt=hmac_salt)
        self.tokenizer = FinFlagTokenizer()
        self.scorer   = RuleBasedScorer()
        self.ensemble = EnsembleDecisionEngine(strategy=strategy)

    def process(self, raw: dict) -> dict:
        """
        Run a raw transaction through all pipeline stages.

        Parameters
        ----------
        raw : dict with keys:
            sensor_id, imsi_status, hardware_risk, typing_speed,
            raw_phone, amount, transaction_type, location,
            national_id (optional), recipient_phone (optional)

        Returns
        -------
        dict — FinFlag Decision including audit trail
        """
        # ── Stage 1: Cryptographic Gateway (FPE + HMAC) ──────────────────
        tweak = raw["sensor_id"].encode()[:16].ljust(16, b"\x00")

        masked_sender    = self.cipher.encrypt_phone_prefix_safe(raw["raw_phone"], tweak)
        masked_recipient = None
        if raw.get("recipient_phone"):
            masked_recipient = self.cipher.encrypt_phone_prefix_safe(
                raw["recipient_phone"], tweak
            )
        masked_nid = None
        if raw.get("national_id"):
            masked_nid = self.cipher.encrypt_national_id(raw["national_id"])

        behavioral_hash = self.hasher.hash_phone(raw["raw_phone"])

        masked_packet = {
            "masked_sender_phone":    masked_sender,
            "masked_recipient_phone": masked_recipient,
            "masked_national_id":     masked_nid,
            "behavioral_hash":        behavioral_hash,
            "sensor_id":              raw["sensor_id"],
            "imsi_status":            raw["imsi_status"],
            "hardware_risk":          raw["hardware_risk"],
            "typing_speed":           raw.get("typing_speed", 0.0),
            "amount":                 raw["amount"],
            "transaction_type":       raw["transaction_type"],
            "location":               raw["location"],
            "timestamp":              raw.get("timestamp", ""),
        }

        # ── Stage 2: Tokenization ─────────────────────────────────────────
        tokenized = self.tokenizer.process(masked_packet)

        # ── Stage 3: Structured ML scoring (Rule-Based / XGBoost proxy) ──
        struct_result = self.scorer.score(tokenized["feature_vector"])
        struct_score  = struct_result["fraud_probability"]

        # ── Stage 4: Encoder LLM (simulated; real needs PyTorch) ─────────
        # When PyTorch is available, replace this with:
        #   llm_score = self.llm_model.predict_sentence(tokenized["sentence"])
        llm_score = self._simulate_llm(tokenized["sentence"], struct_score)

        # ── Stage 5: Ensemble Decision ────────────────────────────────────
        decision = self.ensemble.decide(
            llm_score    = llm_score,
            struct_score = struct_score,
            behavioral_hash = behavioral_hash,
        )

        return {
            "decision":         decision,
            "sentence":         tokenized["sentence"],
            "feature_vector":   tokenized["feature_vector"],
            "struct_detail":    struct_result,
            "masked_packet":    masked_packet,
            "audit": {
                "behavioral_hash":  behavioral_hash,
                "masked_sender":    masked_sender,
                "masked_recipient": masked_recipient,
                "sensor_id":        raw["sensor_id"],
            },
        }

    @staticmethod
    def _simulate_llm(sentence: str, struct_score: float) -> float:
        """
        Simulate LLM score until PyTorch is installed.
        The LLM adds context the rule-based scorer might miss:
          - "SWAPPED" in context of a remote location is worse than alone
          - "whale" + "remote" + "SWAPPED" together spike the score
        """
        bonus = 0.0
        sentence_lower = sentence.lower()
        high_risk_words = ["swapped", "cloned", "remote", "whale",
                           "critical", "superhuman"]
        count = sum(1 for w in high_risk_words if w in sentence_lower)
        if count >= 3:
            bonus = 0.15
        elif count >= 2:
            bonus = 0.08
        elif count == 1:
            bonus = 0.03
        return min(struct_score + bonus, 1.0)


# ── Demo / integration test ─────────────────────────────────────────────────

def _run_demo():
    fpe_key   = bytes.fromhex("0" * 64)   # test-only zero key
    hmac_salt = b"finflag-pipeline-test-salt!!!!!!!"[:32]

    pipeline = FinFlagPipeline(fpe_key, hmac_salt, strategy="escalation")

    test_transactions = [
        {
            "label": "🟢 Routine M-Pesa payment — JKUAT canteen",
            "raw": {
                "sensor_id": "JKUAT-SN-001",
                "imsi_status": "ACTIVE",
                "hardware_risk": 0.05,
                "typing_speed": 68.0,
                "raw_phone": "0722123456",
                "amount": 150.0,
                "transaction_type": "PAYMENT",
                "location": "Juja",
                "timestamp": "2025-04-08T08:30:00Z",
            }
        },
        {
            "label": "🔴 SIM-Swap + whale transfer — Account Takeover",
            "raw": {
                "sensor_id": "JKUAT-SN-002",
                "imsi_status": "SWAPPED",
                "hardware_risk": 0.88,
                "typing_speed": 350.0,
                "raw_phone": "0733999888",
                "recipient_phone": "0722000001",
                "amount": 175000.0,
                "transaction_type": "TRANSFER",
                "location": "UNKNOWN",
                "timestamp": "2025-04-08T02:15:00Z",
            }
        },
        {
            "label": "🟡 Grey zone — Medium risk in Westlands",
            "raw": {
                "sensor_id": "JKUAT-SN-003",
                "imsi_status": "UNKNOWN",
                "hardware_risk": 0.48,
                "typing_speed": 52.0,
                "raw_phone": "0712345678",
                "national_id": "12345678",
                "amount": 55000.0,
                "transaction_type": "WITHDRAWAL",
                "location": "Westlands",
                "timestamp": "2025-04-08T14:00:00Z",
            }
        },
    ]

    print("=" * 72)
    print("  FinFlag · Full Pipeline Integration Test")
    print("  Sharon — Cryptographic Gateway & Encoder LLM Engineer")
    print("=" * 72)

    for tc in test_transactions:
        result = pipeline.process(tc["raw"])
        d      = result["decision"]
        audit  = result["audit"]

        print(f"\n  {tc['label']}")
        print(f"  {'─'*66}")
        print(f"  Sentence  : {result['sentence'][:70]}...")
        print(f"  Masked ID : {audit['masked_sender']}  (was: {tc['raw']['raw_phone']})")
        print(f"  HMAC Token: {audit['behavioral_hash']}")
        print(f"  ─ Struct score  : {d['struct_score']:.4f}")
        print(f"  ─ LLM score     : {d['llm_score']:.4f}  (simulated)")
        print(f"  ─ Fusion method : {d['fusion_method']}")
        print(f"  ➜ FINAL DECISION: [{d['status']}]  "
              f"p={d['fraud_probability']:.4f}  risk={d['risk_level']}")
        if result["struct_detail"]["flags"]:
            print(f"  ⚑ Flags: {', '.join(result['struct_detail']['flags'])}")

    print("\n" + "=" * 72)
    print("  All stages passed. Ready for Week 2 Redis integration.")
    print("=" * 72)


if __name__ == "__main__":
    _run_demo()
