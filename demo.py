"""
demo.py – Role 1 Edge Telemetry Demo Runner

Usage:
    python demo.py

Scenarios tested:
    1. Normal login – LOW risk
    2. New device + SIM swap – HIGH risk
    3. Geo-location jump (Nairobi → Nigeria) – HIGH risk
    4. Late-night login anomaly – SUSPICIOUS
"""

import json
import time
from src.edge_telemetry import EdgeTelemetryModule


def print_section(title: str):
    print("\n" + "═" * 60)
    print(f"  {title}")
    print("═" * 60)


def run_scenario(label: str, telemetry_input: dict, module: EdgeTelemetryModule):
    print_section(f"SCENARIO: {label}")
    result = module.process(telemetry_input)
    print(json.dumps(result, indent=2))
    risk = result["risk_assessment"]
    print(f"\n  ▶  FINAL RISK: {risk['risk_level']}  (score: {risk['risk_score']})")
    print(f"  ▶  ACTION   : {risk['recommendation']}")


def main():
    module = EdgeTelemetryModule()
    now = time.time()

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 1: Normal login from same device, same area, same time
    # Expected: LOW risk
    # ─────────────────────────────────────────────────────────────────
    scenario_1 = {
        "user_id": "USR-001",
        "device_attributes": {
            "model": "Samsung Galaxy A54",
            "android_version": "13",
            "screen_resolution": "1080x2340",
            "cpu_abi": "arm64-v8a",
            "build_fingerprint": "samsung/a54/a54:13/TP1A.220624.014/A546EXXU3CWJ1:user/release-keys"
        },
        "previous_fingerprint": "a3f8c1e2d5b6a7f9e0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3",
        "current_lat":  -1.286389,   # Nairobi
        "current_lon":  36.817223,
        "previous_lat": -1.290000,
        "previous_lon": 36.820000,
        "time_since_last_login_seconds": 86400,  # 24 hours
        "current_imsi":  "63902123456789",
        "previous_imsi": "63902123456789",
        "imsi_change_count_24h": 0,
        "login_hour_history": [9, 10, 9, 11, 10, 9, 10, 9, 10, 10],  # Usually logs in 9-11am
    }

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 2: SIM swap + new device login attempt
    # Expected: HIGH risk
    # ─────────────────────────────────────────────────────────────────
    scenario_2 = {
        "user_id": "USR-002",
        "device_attributes": {
            "model": "Unknown Device X99",   # Unfamiliar hardware
            "android_version": "10",
            "screen_resolution": "720x1560",
            "cpu_abi": "armeabi-v7a",
            "build_fingerprint": "generic/aosp/device:10/QKQ1.191105.002/eng.unknown.20200101:userdebug/test-keys"
        },
        "previous_fingerprint": "a3f8c1e2d5b6a7f9e0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3",
        "current_lat":  -1.286389,
        "current_lon":  36.817223,
        "previous_lat": -1.286389,
        "previous_lon": 36.817223,
        "time_since_last_login_seconds": 600,
        "current_imsi":  "63902999999999",   # IMSI changed!
        "previous_imsi": "63902123456789",
        "imsi_change_timestamp": now - 300,  # Changed 5 mins ago (within 10-min window)
        "imsi_change_count_24h": 2,          # 2 changes in 24h
        "login_hour_history": [9, 10, 9, 11, 10, 9, 10],
    }

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 3: Impossible geo-location jump
    # Expected: HIGH risk
    # ─────────────────────────────────────────────────────────────────
    scenario_3 = {
        "user_id": "USR-003",
        "device_attributes": {
            "model": "Samsung Galaxy A54",
            "android_version": "13",
            "screen_resolution": "1080x2340",
            "cpu_abi": "arm64-v8a",
            "build_fingerprint": "samsung/a54/a54:13/TP1A.220624.014/A546EXXU3CWJ1:user/release-keys"
        },
        "previous_fingerprint": None,  # No previous fingerprint = new device flag
        "current_lat":   6.5244,       # Lagos, Nigeria (far from Kenya!)
        "current_lon":   3.3792,
        "previous_lat": -1.286389,     # Was in Nairobi
        "previous_lon": 36.817223,
        "time_since_last_login_seconds": 300,  # Only 5 minutes ago!
        "current_imsi":  "63902123456789",
        "previous_imsi": "63902123456789",
        "imsi_change_count_24h": 0,
        "login_hour_history": [10, 10, 11, 10, 9, 10],
    }

    # ─────────────────────────────────────────────────────────────────
    # SCENARIO 4: Statistically anomalous login time
    # Expected: MEDIUM / SUSPICIOUS risk
    # ─────────────────────────────────────────────────────────────────
    scenario_4 = {
        "user_id": "USR-004",
        "device_attributes": {
            "model": "Samsung Galaxy A54",
            "android_version": "13",
            "screen_resolution": "1080x2340",
            "cpu_abi": "arm64-v8a",
            "build_fingerprint": "samsung/a54/a54:13/TP1A.220624.014/A546EXXU3CWJ1:user/release-keys"
        },
        "previous_fingerprint": "a3f8c1e2d5b6a7f9e0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3",
        "current_lat":  -1.286389,
        "current_lon":  36.817223,
        "previous_lat": -1.286389,
        "previous_lon": 36.817223,
        "time_since_last_login_seconds": 7200,
        "current_imsi":  "63902123456789",
        "previous_imsi": "63902123456789",
        "imsi_change_count_24h": 0,
        # User always logs in between 9-11am → 3am login is anomalous
        "login_hour_history": [9, 10, 9, 11, 10, 9, 10, 9, 10, 10, 9, 11, 10],
    }

    print("\n" + "█" * 60)
    print("  ROLE 1 – SMART EDGE TELEMETRY & ANOMALY DETECTION")
    print("  FinTech Fraud Detection AI – Demo Runner")
    print("█" * 60)

    run_scenario("Normal Login (Expected: LOW)", scenario_1, module)
    run_scenario("SIM Swap + New Device (Expected: HIGH)", scenario_2, module)
    run_scenario("Geo-Location Jump Nairobi→Lagos (Expected: HIGH)", scenario_3, module)
    run_scenario("Anomalous Login Hour (Expected: MEDIUM)", scenario_4, module)

    print("\n" + "═" * 60)
    print("  Demo complete. See src/edge_telemetry.py for full source.")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
