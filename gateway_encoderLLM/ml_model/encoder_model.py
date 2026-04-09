"""
ml_model/encoder_model.py
==========================
FinFlag · Encoder LLM — Financial Fraud Sequence Classifier
Author: Sharon — Cryptographic Gateway Engineer & Encoder LLM Engineer

ARCHITECTURE OVERVIEW
---------------------
This module implements the "Brain" layer of FinFlag using a BERT-style
Encoder LLM (DistilBERT). It is designed to read sequences of financial
"sentences" produced by the FinFlagTokenizer and predict fraud probability.

Why an Encoder (not a Decoder)?
  Encoders (BERT, DistilBERT, RoBERTa) are trained to UNDERSTAND text, not
  generate it. Fraud detection is a *classification* task — we want the model
  to "read" a transaction and output a score. Decoders (GPT) are for
  generation. Encoders are the right tool here.

Key Innovation (Sharon's Dual-Role Contribution):
  Standard BERT sees "0722891043" as random digits and splits them into
  sub-word tokens: ["072", "##289", "##10", "##43"] — meaningless.

  FinFlag's approach:
  1. The FPE-encrypted number is converted to a SHORT LABEL ("a3f8c1")
     by the tokenizer — this is treated as a single special token.
  2. The full financial SENTENCE is what BERT actually reads, not raw digits.
  3. This preserves BERT's pre-trained semantic understanding ("SWAPPED SIM"
     is suspicious; "remote location" + "whale amount" is a red flag).

Two operating modes:
  - INFERENCE MODE (no PyTorch): Uses a deterministic rule-based scorer
    that mimics what a trained model would output. Works immediately.
  - FULL MODE (requires PyTorch + transformers): Fine-tunes DistilBERT on
    synthetic PaySim data. Activated when torch is installed.
"""

from __future__ import annotations

import json
import math
import hashlib
from typing import Optional

# ── Optional ML dependencies ─────────────────────────────────────────────────

try:
    import torch
    import torch.nn as nn
    from transformers import (
        DistilBertTokenizerFast,
        DistilBertModel,
        DistilBertConfig,
    )
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# ── Risk constants (same as tokenizer for consistency) ───────────────────────

IMSI_RISK = {"ACTIVE": 0.0, "UNKNOWN": 0.3, "SWAPPED": 0.7, "CLONED": 1.0}
AMOUNT_WHALE = 150_000.0


# ═══════════════════════════════════════════════════════════════════════════
#  LAYER 1 — Rule-Based Inference Engine (works without PyTorch)
#  This is the "Structured ML" approximation of the Encoder's output.
#  Yvonne's XGBoost will replace/complement this layer.
# ═══════════════════════════════════════════════════════════════════════════

class RuleBasedScorer:
    """
    Deterministic fraud scorer based on expert rules.

    This is used in two scenarios:
      1. When PyTorch is not installed (development / edge deployment).
      2. As the "Structured ML" baseline to compare against the Encoder LLM.

    Rules are derived from common M-Pesa fraud patterns in Kenya:
      - SIM-swap fraud (IMSI_STATUS = SWAPPED or CLONED)
      - Account Takeover (rapid transfers to new recipients)
      - Unusual location + high amount combinations
    """

    def score(self, feature_vector: dict) -> dict:
        """
        Score a feature vector. Returns fraud probability and explanation.

        Parameters
        ----------
        feature_vector : dict  (output of FinFlagTokenizer._build_features)

        Returns
        -------
        dict with: fraud_probability, risk_level, flags, explanation
        """
        score = 0.0
        flags = []

        # ── SIM / Device signals ──────────────────────────────────────
        imsi_risk = feature_vector.get("imsi_risk", 0)
        if imsi_risk >= 0.7:
            score += 0.40
            flags.append("SIM_SWAP_DETECTED" if imsi_risk == 0.7 else "SIM_CLONED")
        elif imsi_risk >= 0.3:
            score += 0.10
            flags.append("UNKNOWN_SIM_STATUS")

        hw_risk = feature_vector.get("hardware_risk", 0)
        if hw_risk >= 0.75:
            score += 0.20
            flags.append("HIGH_DEVICE_RISK")
        elif hw_risk >= 0.50:
            score += 0.10
            flags.append("MODERATE_DEVICE_RISK")

        # ── Amount signals ────────────────────────────────────────────
        if feature_vector.get("is_whale"):
            score += 0.15
            flags.append("WHALE_TRANSACTION")
        elif feature_vector.get("amount_band_idx", 0) >= 3:
            score += 0.08
            flags.append("LARGE_TRANSACTION")

        if feature_vector.get("is_round_number"):
            score += 0.05
            flags.append("ROUND_NUMBER_AMOUNT")  # common in scripted fraud

        # ── Location signals ──────────────────────────────────────────
        if not feature_vector.get("location_known"):
            score += 0.10
            flags.append("REMOTE_LOCATION")

        # ── Behavioral signals ────────────────────────────────────────
        typing_speed = feature_vector.get("typing_speed", 60)
        if typing_speed > 0 and typing_speed < 10:
            score += 0.10
            flags.append("UNUSUALLY_SLOW_TYPING")   # possible bot
        elif typing_speed > 200:
            score += 0.15
            flags.append("SUPERHUMAN_TYPING_SPEED")  # definite bot

        if feature_vector.get("tx_is_transfer") and \
           feature_vector.get("has_recipient") and \
           feature_vector.get("is_whale"):
            score += 0.10
            flags.append("LARGE_TRANSFER_TO_NEW_RECIPIENT")

        fraud_probability = min(score, 1.0)
        risk_level = self._risk_level(fraud_probability)

        return {
            "fraud_probability": round(fraud_probability, 4),
            "risk_level":        risk_level,
            "status":            "BLOCK" if fraud_probability >= 0.5 else "PASS",
            "flags":             flags,
            "explanation":       self._explain(flags, fraud_probability),
            "model":             "rule_based_v1",
        }

    @staticmethod
    def _risk_level(p: float) -> str:
        if p < 0.2:  return "LOW"
        if p < 0.5:  return "MEDIUM"
        if p < 0.75: return "HIGH"
        return "CRITICAL"

    @staticmethod
    def _explain(flags: list, p: float) -> str:
        if not flags:
            return "No significant risk signals detected."
        top = flags[:3]
        return (
            f"Fraud probability {p:.0%} driven by: {', '.join(top)}. "
            f"{'Immediate block recommended.' if p >= 0.5 else 'Monitor closely.'}"
        )


# ═══════════════════════════════════════════════════════════════════════════
#  LAYER 2 — Encoder LLM (requires PyTorch + transformers)
#  Fine-tuned DistilBERT that reads financial sentences
# ═══════════════════════════════════════════════════════════════════════════

if TORCH_AVAILABLE:

    class FraudClassificationHead(nn.Module):
        """
        Classification head that sits on top of DistilBERT.

        Architecture:
          DistilBERT [CLS] embedding (768-dim)
            → Dropout(0.3)
            → Linear(768 → 256)
            → GELU activation
            → Dropout(0.2)
            → Linear(256 → 1)
            → Sigmoid
            → fraud_probability (scalar 0–1)

        Why [CLS]?
          BERT's [CLS] token aggregates information from the ENTIRE sentence
          through self-attention. It is the standard representation for
          sentence-level classification tasks.
        """

        def __init__(self, hidden_size: int = 768, dropout: float = 0.3):
            super().__init__()
            self.dropout1 = nn.Dropout(dropout)
            self.fc1      = nn.Linear(hidden_size, 256)
            self.act      = nn.GELU()
            self.dropout2 = nn.Dropout(0.2)
            self.fc2      = nn.Linear(256, 1)
            self.sigmoid  = nn.Sigmoid()

        def forward(self, cls_embedding: torch.Tensor) -> torch.Tensor:
            x = self.dropout1(cls_embedding)
            x = self.fc1(x)
            x = self.act(x)
            x = self.dropout2(x)
            x = self.fc2(x)
            return self.sigmoid(x)


    class FinFlagEncoderLLM(nn.Module):
        """
        Full Encoder LLM: DistilBERT backbone + FraudClassificationHead.

        Usage (inference)
        -----------------
        >>> model  = FinFlagEncoderLLM.from_pretrained()  # or .new()
        >>> result = model.predict_sentence(
        ...     "Transaction by user [a3f8c1] at [Juja] [known] location. "
        ...     "Amount: small (4500 KES). Device risk: high. SIM status: SWAPPED."
        ... )
        >>> result["fraud_probability"]   # e.g. 0.873
        >>> result["status"]              # "BLOCK"

        Training (Week 3 sprint)
        --------
        >>> model = FinFlagEncoderLLM.new()
        >>> # model.fine_tune(train_dataloader, val_dataloader, epochs=5)
        """

        MODEL_NAME = "distilbert-base-uncased"
        MAX_LEN    = 128   # max tokens per sentence

        def __init__(self):
            super().__init__()
            config          = DistilBertConfig.from_pretrained(self.MODEL_NAME)
            self.encoder    = DistilBertModel.from_pretrained(self.MODEL_NAME)
            self.classifier = FraudClassificationHead(config.dim)
            self.tokenizer  = DistilBertTokenizerFast.from_pretrained(self.MODEL_NAME)

        @classmethod
        def new(cls) -> "FinFlagEncoderLLM":
            """Create a fresh model with pre-trained BERT weights."""
            return cls()

        @classmethod
        def from_pretrained(cls, checkpoint_path: str) -> "FinFlagEncoderLLM":
            """Load fine-tuned weights from a saved checkpoint."""
            model = cls()
            state = torch.load(checkpoint_path, map_location="cpu")
            model.load_state_dict(state)
            model.eval()
            return model

        def forward(self, input_ids, attention_mask) -> torch.Tensor:
            outputs     = self.encoder(input_ids=input_ids,
                                       attention_mask=attention_mask)
            cls_emb     = outputs.last_hidden_state[:, 0, :]  # [CLS] token
            return self.classifier(cls_emb)

        @torch.no_grad()
        def predict_sentence(self, sentence: str,
                             device: str = "cpu") -> dict:
            """
            Run inference on a single financial sentence.

            Returns a dict matching the FinFlag AI Output schema:
              fraud_probability, status, risk_level, embedding
            """
            self.eval()
            self.to(device)

            encoded = self.tokenizer(
                sentence,
                truncation=True,
                max_length=self.MAX_LEN,
                padding="max_length",
                return_tensors="pt",
            )
            input_ids      = encoded["input_ids"].to(device)
            attention_mask = encoded["attention_mask"].to(device)

            prob  = self(input_ids, attention_mask).item()
            level = self._risk_level(prob)

            return {
                "fraud_probability": round(prob, 4),
                "risk_level":        level,
                "status":            "BLOCK" if prob >= 0.5 else "PASS",
                "model":             "distilbert-finflag-v1",
            }

        def fine_tune(self, train_loader, val_loader,
                      epochs: int = 5, lr: float = 2e-5,
                      device: str = "cpu"):
            """
            Fine-tune on labelled PaySim data.

            Expected DataLoader format:
              Each batch: {"input_ids", "attention_mask", "labels"}
              labels: float tensor of shape (batch,) with 0.0=legit, 1.0=fraud

            Training strategy:
              - Freeze BERT backbone for epoch 1 (train head only → fast)
              - Unfreeze all layers from epoch 2 onwards (full fine-tune)
              - Binary Cross-Entropy loss (BCELoss)
              - AdamW optimizer with linear warmup
            """
            self.to(device)
            optimizer = torch.optim.AdamW(self.parameters(), lr=lr,
                                          weight_decay=0.01)
            criterion = nn.BCELoss()

            for epoch in range(epochs):
                # Freeze backbone on epoch 0
                for param in self.encoder.parameters():
                    param.requires_grad = (epoch > 0)

                self.train()
                total_loss = 0.0
                for batch in train_loader:
                    optimizer.zero_grad()
                    ids   = batch["input_ids"].to(device)
                    mask  = batch["attention_mask"].to(device)
                    labels = batch["labels"].float().unsqueeze(1).to(device)

                    preds = self(ids, mask)
                    loss  = criterion(preds, labels)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.parameters(), 1.0)
                    optimizer.step()
                    total_loss += loss.item()

                avg_loss = total_loss / max(len(train_loader), 1)
                val_acc  = self._evaluate(val_loader, device)
                print(f"  Epoch {epoch+1}/{epochs} — "
                      f"loss: {avg_loss:.4f}  val_acc: {val_acc:.3f}")

        @torch.no_grad()
        def _evaluate(self, loader, device: str) -> float:
            self.eval()
            correct = total = 0
            for batch in loader:
                ids   = batch["input_ids"].to(device)
                mask  = batch["attention_mask"].to(device)
                labels = batch["labels"].to(device)
                preds = (self(ids, mask).squeeze() >= 0.5).long()
                correct += (preds == labels).sum().item()
                total   += labels.size(0)
            return correct / max(total, 1)

        @staticmethod
        def _risk_level(p: float) -> str:
            if p < 0.2:  return "LOW"
            if p < 0.5:  return "MEDIUM"
            if p < 0.75: return "HIGH"
            return "CRITICAL"


# ═══════════════════════════════════════════════════════════════════════════
#  LAYER 3 — Ensemble Decision Engine
#  Combines Rule-Based + Encoder LLM scores into a final FinFlag Decision
# ═══════════════════════════════════════════════════════════════════════════

class EnsembleDecisionEngine:
    """
    The "Two-Brain" meta-classifier.

    Combines:
      Brain A (Sharon) — Encoder LLM score (sequence/context understanding)
      Brain B (Yvonne) — Structured ML score (hard numerical rules)

    into a final weighted fraud probability.

    Three fusion strategies (set via `strategy` param):
      "weighted_avg"  → w_llm * p_llm + w_struct * p_struct  (default)
      "max"           → max(p_llm, p_struct)  (most conservative)
      "escalation"    → use Structured ML; only call LLM if score is "grey"

    The "escalation" strategy saves GPU compute for clear-cut transactions
    (Member 3's performance goal: 1,000+ tx/sec).
    """

    GREY_ZONE_LOW  = 0.25
    GREY_ZONE_HIGH = 0.65

    def __init__(self,
                 strategy: str = "weighted_avg",
                 llm_weight: float = 0.55,
                 struct_weight: float = 0.45):
        self.strategy      = strategy
        self.llm_weight    = llm_weight
        self.struct_weight = struct_weight

    def decide(self,
               llm_score: Optional[float],
               struct_score: float,
               behavioral_hash: str = "") -> dict:
        """
        Produce the final FinFlag Decision.

        Parameters
        ----------
        llm_score    : fraud probability from Encoder LLM (None if not run)
        struct_score : fraud probability from Structured ML / Rule-Based
        behavioral_hash : HMAC token for audit linking

        Returns
        -------
        dict — the AI Output block (matches FinFlag Data Dictionary)
        """
        if self.strategy == "escalation":
            final_score, method = self._escalation(llm_score, struct_score)
        elif self.strategy == "max" or llm_score is None:
            final_score = max(struct_score, llm_score or 0.0)
            method = "max_fusion"
        else:
            final_score = (self.llm_weight * llm_score +
                           self.struct_weight * struct_score)
            method = "weighted_avg_fusion"

        final_score = min(final_score, 1.0)
        status      = "BLOCK" if final_score >= 0.5 else "PASS"
        risk_level  = self._risk_level(final_score)

        return {
            "fraud_probability": round(final_score, 4),
            "status":            status,
            "risk_level":        risk_level,
            "fusion_method":     method,
            "llm_score":         round(llm_score, 4) if llm_score is not None else None,
            "struct_score":      round(struct_score, 4),
            "behavioral_hash":   behavioral_hash,
        }

    def _escalation(self, llm_score, struct_score):
        """
        Escalation strategy: use Structured ML first.
        Only invoke LLM if the score is in the 'grey zone'.
        """
        if not (self.GREY_ZONE_LOW <= struct_score <= self.GREY_ZONE_HIGH):
            return struct_score, "struct_only (clear)"
        if llm_score is not None:
            combined = self.llm_weight * llm_score + self.struct_weight * struct_score
            return combined, "escalated_to_llm"
        return struct_score, "struct_only (llm_unavailable)"

    @staticmethod
    def _risk_level(p: float) -> str:
        if p < 0.2:  return "LOW"
        if p < 0.5:  return "MEDIUM"
        if p < 0.75: return "HIGH"
        return "CRITICAL"


# ═══════════════════════════════════════════════════════════════════════════
#  Self-test / demo
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 68)
    print("  FinFlag Encoder LLM — System Self-Test")
    print(f"  PyTorch available: {TORCH_AVAILABLE}")
    print("=" * 68)

    # Simulate tokenizer output (normally comes from tokenizer_service.py)
    test_cases = [
        {
            "label": "🟢 Normal transaction — JKUAT student",
            "sentence": (
                "Transaction by user [a3f8c1] at [Juja] [known] location. "
                "Amount: micro (200 KES). Device risk: low. "
                "SIM status: ACTIVE. Type: PAYMENT. Recipient: [self]."
            ),
            "features": {
                "amount": 200, "hardware_risk": 0.05, "imsi_risk": 0.0,
                "sim_swapped": 0, "sim_cloned": 0, "location_known": 1,
                "is_whale": 0, "is_round_number": 0, "typing_speed": 72,
                "has_recipient": 0, "tx_is_transfer": 0, "tx_is_payment": 1,
                "tx_is_withdrawal": 0, "tx_is_deposit": 0,
                "amount_log": 5.3, "amount_band_idx": 0,
            },
        },
        {
            "label": "🔴 SIM-Swap + Whale transfer — Account Takeover",
            "sentence": (
                "Transaction by user [ff2a89] at [UNKNOWN] [remote] location. "
                "Amount: whale (180000 KES). Device risk: critical. "
                "SIM status: SWAPPED. Type: TRANSFER. Recipient: [b9c341]."
            ),
            "features": {
                "amount": 180000, "hardware_risk": 0.91, "imsi_risk": 0.7,
                "sim_swapped": 1, "sim_cloned": 0, "location_known": 0,
                "is_whale": 1, "is_round_number": 0, "typing_speed": 312,
                "has_recipient": 1, "tx_is_transfer": 1, "tx_is_payment": 0,
                "tx_is_withdrawal": 0, "tx_is_deposit": 0,
                "amount_log": 12.1, "amount_band_idx": 4,
            },
        },
        {
            "label": "🟡 Grey zone — Medium risk, needs LLM investigation",
            "sentence": (
                "Transaction by user [c1d4e9] at [Westlands] [known] location. "
                "Amount: large (60000 KES). Device risk: moderate. "
                "SIM status: UNKNOWN. Type: WITHDRAWAL. Recipient: [self]."
            ),
            "features": {
                "amount": 60000, "hardware_risk": 0.45, "imsi_risk": 0.3,
                "sim_swapped": 0, "sim_cloned": 0, "location_known": 1,
                "is_whale": 0, "is_round_number": 1, "typing_speed": 55,
                "has_recipient": 0, "tx_is_transfer": 0, "tx_is_payment": 0,
                "tx_is_withdrawal": 1, "tx_is_deposit": 0,
                "amount_log": 11.0, "amount_band_idx": 3,
            },
        },
    ]

    scorer   = RuleBasedScorer()
    ensemble = EnsembleDecisionEngine(strategy="escalation")

    for tc in test_cases:
        struct_result = scorer.score(tc["features"])
        struct_score  = struct_result["fraud_probability"]

        # Simulate LLM score (would come from FinFlagEncoderLLM.predict_sentence)
        # For demo: LLM adds slight additional signal based on sentence keywords
        llm_sim = struct_score + (0.1 if "SWAPPED" in tc["sentence"] else 0)
        llm_sim = (0.05 if "micro" in tc["sentence"] else llm_sim)

        final = ensemble.decide(llm_sim, struct_score,
                                behavioral_hash="FF-demo-hash")

        print(f"\n  {tc['label']}")
        print(f"    Sentence    : {tc['sentence'][:65]}...")
        print(f"    Struct score: {struct_score:.4f}  Flags: {struct_result['flags']}")
        print(f"    LLM score   : {llm_sim:.4f}  (simulated — real needs PyTorch)")
        print(f"    ➜ FINAL     : {final['fraud_probability']:.4f}  "
              f"[{final['status']}]  via {final['fusion_method']}")

    print("\n" + "=" * 68)
    if not TORCH_AVAILABLE:
        print("  ⚠  Install PyTorch to enable full Encoder LLM:")
        print("     pip install torch transformers")
    print("=" * 68)
