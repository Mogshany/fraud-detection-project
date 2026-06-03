"""
Role 1 – Smart Edge Telemetry & Anomaly Detection Module
=========================================================
FinTech Fraud Detection AI – Final Year CS/AI/FinTech Project

Computational Techniques Implemented:
1. Device Fingerprint Hashing & Similarity Analysis (SHA-256 + Hamming Distance)
2. Geo-location Risk Scoring (Haversine Formula)
3. SIM Lifecycle Anomaly Detection (Rule-Based Inference System)
4. Statistical Anomaly Detection (Z-Score + Moving Average)
5. Time-Series Behaviour Analysis (Sliding Window Profiling)
6. Edge Risk Scoring Algorithm (Weighted Formula)
7. Lightweight ML Model (Logistic Regression – Optional)

Output:
    A structured JSON payload with a fraud risk score (LOW / MEDIUM / HIGH)
    ready to be forwarded to Role 2 (Cryptographic Gateway).
"""

import hashlib
import json
import math
import time
import statistics
from datetime import datetime
from typing import Optional
from collections import deque


# ─────────────────────────────────────────────
# 1. DEVICE FINGERPRINT ENGINE
# ─────────────────────────────────────────────

class DeviceFingerprintEngine:
    """
    Hashes raw device attributes into a stable fingerprint using SHA-256.
    Compares current fingerprint against a known previous fingerprint
    using Hamming Distance on the binary hash representation.
    """

    def generate_fingerprint(self, device_data: dict) -> str:
        """
        Generates a SHA-256 fingerprint from device attributes.

        Args:
            device_data: dict containing device hardware fields.

        Returns:
            A 64-character hex SHA-256 hash string.
        """
        canonical = json.dumps(device_data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def hamming_distance(self, hash_a: str, hash_b: str) -> int:
        """
        Computes the bit-level Hamming Distance between two hex SHA-256 hashes.
        A higher distance means the fingerprints are more different.

        Args:
            hash_a: Previous known fingerprint (hex string).
            hash_b: Current fingerprint (hex string).

        Returns:
            Integer bit-difference count (0 = identical, 256 = completely different).
        """
        int_a = int(hash_a, 16)
        int_b = int(hash_b, 16)
        xor = int_a ^ int_b
        return bin(xor).count("1")

    def analyze(self, current_data: dict, previous_fingerprint: Optional[str]) -> dict:
        """
        Full device fingerprint analysis.

        Returns:
            {
                "fingerprint": str,
                "is_new_device": bool,
                "similarity_score": float,  # 0.0 (different) → 1.0 (identical)
                "risk_flag": str             # "NONE" | "SUSPICIOUS" | "HIGH"
            }
        """
        current_fp = self.generate_fingerprint(current_data)

        if previous_fingerprint is None:
            return {
                "fingerprint": current_fp,
                "is_new_device": True,
                "similarity_score": 0.0,
                "risk_flag": "SUSPICIOUS",
                "detail": "First-time device – no baseline for comparison."
            }

        distance = self.hamming_distance(previous_fingerprint, current_fp)
        max_bits = 256  # SHA-256 produces 256 bits
        similarity = 1.0 - (distance / max_bits)

        if similarity == 1.0:
            risk_flag = "NONE"
        elif similarity >= 0.85:
            risk_flag = "SUSPICIOUS"
        else:
            risk_flag = "HIGH"

        return {
            "fingerprint": current_fp,
            "is_new_device": current_fp != previous_fingerprint,
            "hamming_distance": distance,
            "similarity_score": round(similarity, 4),
            "risk_flag": risk_flag,
            "detail": f"Fingerprint similarity: {similarity:.1%}"
        }


# ─────────────────────────────────────────────
# 2. GEO-LOCATION RISK ENGINE (HAVERSINE)
# ─────────────────────────────────────────────

class GeoLocationRiskEngine:
    """
    Computes the physical distance between two GPS coordinates
    using the Haversine Formula and flags impossible travel speeds.
    """

    EARTH_RADIUS_KM = 6371.0

    # Kenya-specific known safe zones (city lat/lon, radius_km)
    KNOWN_SAFE_ZONES = {
        "Nairobi":  (-1.286389,  36.817223, 50),
        "Mombasa":  (-4.043740,  39.668206, 40),
        "Kisumu":   (-0.091702,  34.767956, 30),
        "Nakuru":   (-0.303099,  36.080026, 30),
    }

    def haversine_distance(self, lat1: float, lon1: float,
                           lat2: float, lon2: float) -> float:
        """
        Calculates the great-circle distance between two GPS points in kilometres.

        Uses the Haversine formula:
            a = sin²(Δlat/2) + cos(lat1)·cos(lat2)·sin²(Δlon/2)
            c = 2·atan2(√a, √(1−a))
            d = R · c
        """
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (math.sin(dlat / 2) ** 2
             + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return self.EARTH_RADIUS_KM * c

    def is_in_safe_zone(self, lat: float, lon: float) -> Optional[str]:
        """Returns the name of a safe zone if the coordinate falls within one."""
        for city, (city_lat, city_lon, radius) in self.KNOWN_SAFE_ZONES.items():
            if self.haversine_distance(lat, lon, city_lat, city_lon) <= radius:
                return city
        return None

    def analyze(self, current_lat: float, current_lon: float,
                prev_lat: Optional[float], prev_lon: Optional[float],
                time_delta_seconds: float) -> dict:
        """
        Full geo-location risk analysis.

        Returns risk assessment including impossible travel detection.
        """
        safe_zone = self.is_in_safe_zone(current_lat, current_lon)

        if prev_lat is None or prev_lon is None:
            return {
                "current_location": {"lat": current_lat, "lon": current_lon},
                "safe_zone": safe_zone,
                "distance_km": None,
                "speed_kmh": None,
                "risk_flag": "SUSPICIOUS",
                "detail": "No previous location baseline available."
            }

        distance_km = self.haversine_distance(
            prev_lat, prev_lon, current_lat, current_lon
        )

        speed_kmh = (distance_km / (time_delta_seconds / 3600)
                     if time_delta_seconds > 0 else float("inf"))

        # Impossible travel: commercial aircraft max ~900 km/h
        if speed_kmh > 900:
            risk_flag = "HIGH"
            detail = (f"Impossible travel: {distance_km:.1f} km in "
                      f"{time_delta_seconds:.0f}s ({speed_kmh:.0f} km/h).")
        elif distance_km > 1000:
            risk_flag = "HIGH"
            detail = f"Location jump of {distance_km:.1f} km detected."
        elif distance_km > 200:
            risk_flag = "SUSPICIOUS"
            detail = f"Unusual distance: {distance_km:.1f} km from last login."
        else:
            risk_flag = "NONE"
            detail = f"Normal movement: {distance_km:.1f} km."

        return {
            "current_location": {"lat": current_lat, "lon": current_lon},
            "previous_location": {"lat": prev_lat, "lon": prev_lon},
            "safe_zone": safe_zone,
            "distance_km": round(distance_km, 2),
            "speed_kmh": round(speed_kmh, 2) if speed_kmh != float("inf") else "INFINITE",
            "risk_flag": risk_flag,
            "detail": detail
        }


# ─────────────────────────────────────────────
# 3. SIM LIFECYCLE ANOMALY ENGINE
# ─────────────────────────────────────────────

class SIMLifecycleEngine:
    """
    Rule-Based Inference System for SIM Swap / IMSI change detection.
    Evaluates IMSI change frequency and time proximity to login attempts.
    """

    # Rule thresholds
    MAX_IMSI_CHANGES_PER_DAY = 1
    HIGH_RISK_WINDOW_MINUTES = 10  # If IMSI changed within this window → HIGH risk

    def analyze(self, current_imsi: str,
                previous_imsi: Optional[str],
                imsi_change_timestamp: Optional[float],
                login_timestamp: float,
                imsi_change_count_24h: int) -> dict:
        """
        Applies rule-based SIM lifecycle inference.

        Rules:
            Rule 1: If IMSI changed AND within HIGH_RISK_WINDOW_MINUTES of login → HIGH
            Rule 2: If IMSI changed more than MAX_IMSI_CHANGES_PER_DAY → SUSPICIOUS
            Rule 3: If IMSI changed but outside risk window → SUSPICIOUS
            Rule 4: No change → NONE

        Returns:
            Structured risk assessment with the triggered rule.
        """
        imsi_changed = (previous_imsi is not None and current_imsi != previous_imsi)

        if not imsi_changed:
            return {
                "imsi_changed": False,
                "change_count_24h": imsi_change_count_24h,
                "risk_flag": "NONE",
                "triggered_rule": None,
                "detail": "IMSI stable. No SIM swap detected."
            }

        # Time proximity check
        minutes_since_change = None
        if imsi_change_timestamp:
            delta_seconds = login_timestamp - imsi_change_timestamp
            minutes_since_change = delta_seconds / 60

        # Rule evaluation (priority order)
        if (minutes_since_change is not None
                and 0 <= minutes_since_change <= self.HIGH_RISK_WINDOW_MINUTES):
            risk_flag = "HIGH"
            rule = "Rule 1: IMSI change occurred within high-risk login window."

        elif imsi_change_count_24h > self.MAX_IMSI_CHANGES_PER_DAY:
            risk_flag = "HIGH"
            rule = f"Rule 2: {imsi_change_count_24h} IMSI changes in 24h (max: {self.MAX_IMSI_CHANGES_PER_DAY})."

        else:
            risk_flag = "SUSPICIOUS"
            rule = "Rule 3: IMSI changed but outside immediate risk window."

        return {
            "imsi_changed": True,
            "previous_imsi": previous_imsi,
            "current_imsi": current_imsi,
            "minutes_since_change": round(minutes_since_change, 1) if minutes_since_change is not None else None,
            "change_count_24h": imsi_change_count_24h,
            "risk_flag": risk_flag,
            "triggered_rule": rule,
            "detail": rule
        }


# ─────────────────────────────────────────────
# 4. STATISTICAL ANOMALY ENGINE (Z-SCORE)
# ─────────────────────────────────────────────

class StatisticalAnomalyEngine:
    """
    Detects statistical anomalies in behavioural signals using:
      - Z-Score Analysis: measures how many standard deviations a value
        is from the user's historical mean.
      - Sliding Window Moving Average: smooths time-series login activity.
    """

    Z_SCORE_THRESHOLD = 2.5  # Values beyond ±2.5σ are flagged

    def z_score(self, value: float, history: list) -> Optional[float]:
        """
        Computes the Z-score for a value against a history array.

        Formula: z = (x - μ) / σ
        """
        if len(history) < 2:
            return None
        mean = statistics.mean(history)
        stdev = statistics.stdev(history)
        if stdev == 0:
            return 0.0
        return (value - mean) / stdev

    def sliding_window_average(self, series: list, window: int = 7) -> float:
        """
        Computes the moving average over the last `window` elements.
        Used to detect unusual spikes in login frequency.
        """
        if not series:
            return 0.0
        window_data = series[-window:]
        return sum(window_data) / len(window_data)

    def analyze_login_hour(self, current_hour: int, hour_history: list) -> dict:
        """
        Detects if the login hour is statistically anomalous vs user history.

        Args:
            current_hour: 0–23 integer (24h format).
            hour_history: List of previous login hours for this user.

        Returns:
            Risk assessment with Z-score value.
        """
        z = self.z_score(current_hour, hour_history)

        if z is None:
            return {
                "current_hour": current_hour,
                "z_score": None,
                "risk_flag": "SUSPICIOUS",
                "detail": "Insufficient history for statistical analysis."
            }

        abs_z = abs(z)
        if abs_z > self.Z_SCORE_THRESHOLD:
            risk_flag = "HIGH" if abs_z > 3.5 else "SUSPICIOUS"
            detail = f"Login at hour {current_hour} is {abs_z:.1f}σ from normal (Z={z:.2f})."
        else:
            risk_flag = "NONE"
            detail = f"Login hour within normal range (Z={z:.2f})."

        return {
            "current_hour": current_hour,
            "z_score": round(z, 4),
            "mean_login_hour": round(statistics.mean(hour_history), 1),
            "risk_flag": risk_flag,
            "detail": detail
        }

    def analyze_transaction_velocity(self, recent_counts: list, window: int = 7) -> dict:
        """
        Detects abnormal transaction velocity using sliding window analysis.
        """
        avg = self.sliding_window_average(recent_counts, window)
        current = recent_counts[-1] if recent_counts else 0

        if avg == 0:
            return {
                "current_count": current,
                "window_average": avg,
                "risk_flag": "NONE",
                "detail": "No prior transaction velocity baseline."
            }

        ratio = current / avg

        if ratio > 3.0:
            risk_flag = "HIGH"
            detail = f"Transaction velocity {ratio:.1f}× above {window}-day average."
        elif ratio > 1.8:
            risk_flag = "SUSPICIOUS"
            detail = f"Transaction velocity {ratio:.1f}× above average."
        else:
            risk_flag = "NONE"
            detail = f"Transaction velocity normal ({ratio:.1f}× average)."

        return {
            "current_count": current,
            "window_average": round(avg, 2),
            "velocity_ratio": round(ratio, 2),
            "risk_flag": risk_flag,
            "detail": detail
        }


# ─────────────────────────────────────────────
# 5. EDGE RISK SCORING ALGORITHM
# ─────────────────────────────────────────────

class EdgeRiskScorer:
    """
    Aggregates risk signals from all sub-engines into a single weighted
    risk score and produces a final LOW / MEDIUM / HIGH classification.

    Weights (must sum to 1.0):
        Device Fingerprint Change : 0.35
        SIM / IMSI Change         : 0.30
        Geo-location Anomaly      : 0.20
        Statistical Time Anomaly  : 0.15
    """

    WEIGHTS = {
        "device":    0.35,
        "sim":       0.30,
        "location":  0.20,
        "time":      0.15,
    }

    FLAG_SCORES = {
        "NONE":       0.0,
        "SUSPICIOUS": 0.5,
        "HIGH":       1.0,
    }

    def score(self, device_flag: str, sim_flag: str,
              location_flag: str, time_flag: str) -> dict:
        """
        Computes the weighted Edge Risk Score.

        Formula:
            risk = (device_score × 0.35) + (sim_score × 0.30)
                 + (location_score × 0.20) + (time_score × 0.15)

        Returns:
            {
                "risk_score": float,       # 0.0 → 1.0
                "risk_level": str,         # "LOW" | "MEDIUM" | "HIGH"
                "component_scores": dict,
                "recommendation": str
            }
        """
        scores = {
            "device":   self.FLAG_SCORES.get(device_flag, 0),
            "sim":      self.FLAG_SCORES.get(sim_flag, 0),
            "location": self.FLAG_SCORES.get(location_flag, 0),
            "time":     self.FLAG_SCORES.get(time_flag, 0),
        }

        risk_score = sum(scores[k] * self.WEIGHTS[k] for k in scores)

        if risk_score >= 0.65:
            risk_level = "HIGH"
            recommendation = "BLOCK – Forward to Role 4 for deep ML analysis."
        elif risk_score >= 0.35:
            risk_level = "MEDIUM"
            recommendation = "CHALLENGE – Require additional authentication (OTP/Biometric)."
        else:
            risk_level = "LOW"
            recommendation = "ALLOW – Forward encrypted payload to Role 2."

        return {
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "component_scores": {k: {"raw": scores[k], "weighted": round(scores[k] * self.WEIGHTS[k], 4)}
                                 for k in scores},
            "recommendation": recommendation
        }


# ─────────────────────────────────────────────
# 6. MAIN ORCHESTRATOR
# ─────────────────────────────────────────────

class EdgeTelemetryModule:
    """
    Main orchestrator for Role 1 – Smart Edge Telemetry & Anomaly Detection.

    Coordinates all sub-engines and assembles the final JSON payload
    for transmission to Role 2 (Cryptographic Gateway).
    """

    def __init__(self):
        self.fingerprint_engine = DeviceFingerprintEngine()
        self.geo_engine = GeoLocationRiskEngine()
        self.sim_engine = SIMLifecycleEngine()
        self.stat_engine = StatisticalAnomalyEngine()
        self.risk_scorer = EdgeRiskScorer()

    def process(self, telemetry_input: dict) -> dict:
        """
        Full pipeline execution.

        Args:
            telemetry_input: Raw sensor data from the mobile device.

        Returns:
            Structured JSON payload with risk score ready for Role 2.
        """
        timestamp = time.time()
        login_dt = datetime.utcfromtimestamp(timestamp)

        # ── 1. Device Fingerprint Analysis ──────────────────────────────
        device_result = self.fingerprint_engine.analyze(
            current_data=telemetry_input.get("device_attributes", {}),
            previous_fingerprint=telemetry_input.get("previous_fingerprint")
        )

        # ── 2. Geo-Location Risk Analysis ───────────────────────────────
        geo_result = self.geo_engine.analyze(
            current_lat=telemetry_input["current_lat"],
            current_lon=telemetry_input["current_lon"],
            prev_lat=telemetry_input.get("previous_lat"),
            prev_lon=telemetry_input.get("previous_lon"),
            time_delta_seconds=telemetry_input.get("time_since_last_login_seconds", 3600)
        )

        # ── 3. SIM Lifecycle Analysis ────────────────────────────────────
        sim_result = self.sim_engine.analyze(
            current_imsi=telemetry_input["current_imsi"],
            previous_imsi=telemetry_input.get("previous_imsi"),
            imsi_change_timestamp=telemetry_input.get("imsi_change_timestamp"),
            login_timestamp=timestamp,
            imsi_change_count_24h=telemetry_input.get("imsi_change_count_24h", 0)
        )

        # ── 4. Statistical Time Anomaly Analysis ─────────────────────────
        time_result = self.stat_engine.analyze_login_hour(
            current_hour=login_dt.hour,
            hour_history=telemetry_input.get("login_hour_history", [])
        )

        # ── 5. Edge Risk Score Computation ───────────────────────────────
        risk_result = self.risk_scorer.score(
            device_flag=device_result["risk_flag"],
            sim_flag=sim_result["risk_flag"],
            location_flag=geo_result["risk_flag"],
            time_flag=time_result["risk_flag"]
        )

        # ── 6. Assemble Final Payload ────────────────────────────────────
        payload = {
            "metadata": {
                "module": "Role1-EdgeTelemetry",
                "version": "1.0.0",
                "timestamp_utc": login_dt.isoformat() + "Z",
                "user_id": telemetry_input.get("user_id", "UNKNOWN")
            },
            "analyses": {
                "device_fingerprint": device_result,
                "geo_location": geo_result,
                "sim_lifecycle": sim_result,
                "statistical_time": time_result,
            },
            "risk_assessment": risk_result,
            "forward_to_role2": risk_result["risk_level"] != "HIGH"
        }

        return payload
