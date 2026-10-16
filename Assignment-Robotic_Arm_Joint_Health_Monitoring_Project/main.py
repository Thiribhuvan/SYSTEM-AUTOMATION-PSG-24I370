
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "historical_readings.csv"
LOG_PATH = BASE_DIR / "maintenance_log.txt"
OUTPUT_PATH = BASE_DIR / "arm_decisions.json"
CURRENT_PATH = BASE_DIR / "current_readings.csv"


LIMITS = {
    "torque_nm": {"warning": 70.0, "danger": 100.0},
    "temperature_c": {"warning": 70.0, "danger": 90.0},
    "vibration_mm_s": {"warning": 5.0, "danger": 9.0},
}
JOINTS = ("shoulder", "elbow", "wrist")
ARMS = tuple(f"ARM-{i:02d}" for i in range(1, 7))


TORQUE_SPOOF_ABS_TOLERANCE = 18.0
RECENT_HISTORY_SIZE = 5
SPOOF_KEYWORDS = (
    "sensor disconnected", "sensor fault", "reading frozen", "flatline",
    "tampering", "spoof", "calibration failure", "implausible reading",
)

def load_csv(path: Path = DATASET_PATH) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for key in ("torque_nm", "temperature_c", "vibration_mm_s", "wear_label"):
                row[key] = float(row[key]) if key != "wear_label" else int(row[key])
            rows.append(row)
    if not rows:
        raise ValueError(f"No historical readings found in {path}")
    return rows

def train_predictor(rows: list[dict[str, Any]]) -> dict[str, Any]:
  
    feature_names = ("torque_nm", "temperature_c", "vibration_mm_s")
    means = {}
    stds = {}
    for name in feature_names:
        values = [float(r[name]) for r in rows]
        means[name] = sum(values) / len(values)
        variance = sum((x - means[name]) ** 2 for x in values) / max(1, len(values) - 1)
        stds[name] = variance ** 0.5 or 1.0

    groups = {0: [], 1: []}
    for r in rows:
        groups[int(r["wear_label"])].append(r)
    if not groups[0] or not groups[1]:
        raise ValueError("Historical dataset must contain both wear_label 0 and 1.")

    centroids = {}
    for label, group in groups.items():
        centroids[str(label)] = {
            name: sum((float(r[name]) - means[name]) / stds[name] for r in group) / len(group)
            for name in feature_names
        }
    return {"feature_names": feature_names, "means": means, "stds": stds, "centroids": centroids}

def predict_wear(model: dict[str, Any], reading: dict[str, Any]) -> tuple[int, float]:
   
    z = {
        name: (float(reading[name]) - model["means"][name]) / model["stds"][name]
        for name in model["feature_names"]
    }
    distances = {}
    for label, centroid in model["centroids"].items():
        distances[int(label)] = sum((z[n] - centroid[n]) ** 2 for n in model["feature_names"]) ** 0.5
    predicted = min(distances, key=distances.get)
    d0, d1 = distances[0], distances[1]
    
    risk_score = d0 / (d0 + d1) if d0 + d1 else 0.5
    return predicted, risk_score

def load_maintenance_notes(path: Path = LOG_PATH) -> list[dict[str, str]]:
    notes = []
    pattern = re.compile(r"^\[(?P<timestamp>[^\]]+)\]\s+(?P<arm>ARM-\d{2})\s+(?P<joint>shoulder|elbow|wrist|all)\s*:\s*(?P<note>.+)$", re.I)
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = pattern.match(line)
            if match:
                item = {k: v for k, v in match.groupdict().items()}
                item["joint"] = item["joint"].lower()
                item["note"] = item["note"].lower()
                notes.append(item)
            else:
                print(f"WARNING: Ignoring malformed maintenance-log line: {line}")
    return notes

def detect_spoof(readings: list[dict[str, Any]]) -> list[str]:
  
    flags: list[str] = []
    by_joint: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in readings:
        by_joint[(r["arm_id"], r["joint"])].append(r)

    for (arm, joint), history in by_joint.items():
        ordered = sorted(history, key=lambda r: r["timestamp"])
        if len(ordered) >= RECENT_HISTORY_SIZE:
            tail = ordered[-RECENT_HISTORY_SIZE:]
            torques = [float(r["torque_nm"]) for r in tail]
            if max(torques) - min(torques) < 0.05 and torques[0] > LIMITS["torque_nm"]["warning"]:
                flags.append(f"{arm}/{joint}: torque reading is flatlined across recent samples")

    for r in readings:
        torque = float(r["torque_nm"])
        temp = float(r["temperature_c"])
        vib = float(r["vibration_mm_s"])
        if (torque >= LIMITS["torque_nm"]["warning"]
                and temp < 45.0 and vib < 2.0):
            flags.append(
                f'{r["arm_id"]}/{r["joint"]}: high torque conflicts with low temperature and vibration'
            )

    return sorted(set(flags))

def notes_for_arm(notes: list[dict[str, str]], arm_id: str) -> list[dict[str, str]]:
    return [n for n in notes if n["arm"].upper() == arm_id.upper()]

def note_risk(notes: list[dict[str, str]], arm_id: str) -> tuple[bool, bool, list[str]]:
    """Return (maintenance_concern, sensor_concern, matched phrases)."""
    maintenance_terms = (
        "grinding", "unusual vibration", "overheating", "hot", "bearing noise",
        "backlash", "lubrication", "wear", "stiff", "metal particles", "repeated fault",
    )
    sensor_terms = SPOOF_KEYWORDS
    relevant = []
    maintenance_concern = False
    sensor_concern = False
    for n in notes_for_arm(notes, arm_id):
        note = n["note"]
        matched = [term for term in maintenance_terms + sensor_terms if term in note]
        if matched:
            relevant.append(f'{n["joint"]}: {n["note"]} (matched: {", ".join(matched)})')
        if any(term in note for term in maintenance_terms):
            maintenance_concern = True
        if any(term in note for term in sensor_terms):
            sensor_concern = True
    return maintenance_concern, sensor_concern, relevant

def evaluate_arm(
    arm_id: str,
    readings: list[dict[str, Any]],
    model: dict[str, Any],
    notes: list[dict[str, str]],
) -> dict[str, Any]:
    arm_readings = [r for r in readings if r["arm_id"] == arm_id]
    if not arm_readings:
        return {"arm_id": arm_id, "decision": "MONITOR", "reasons": ["No current readings available"]}

    
    dangerous = []
    for r in arm_readings:
        for feature, spec in LIMITS.items():
            if float(r[feature]) >= spec["danger"]:
                dangerous.append(
                    f'{r["joint"]} {feature}={float(r[feature]):.2f} crosses danger limit {spec["danger"]:.2f}'
                )
    if dangerous:
        return {
            "arm_id": arm_id, "decision": "EMERGENCY_STOP",
            "reasons": ["Deterministic danger threshold crossed; ML was not consulted."] + dangerous,
        }

    predictions = []
    for r in arm_readings:
        label, score = predict_wear(model, r)
        predictions.append({"joint": r["joint"], "predicted_wear": label, "risk_score": round(score, 3)})

    spoof_flags = detect_spoof(arm_readings)
    maintenance_concern, sensor_concern, matched_notes = note_risk(notes, arm_id)

    warning_values = []
    for r in arm_readings:
        for feature, spec in LIMITS.items():
            if float(r[feature]) >= spec["warning"]:
                warning_values.append(f'{r["joint"]} {feature}={float(r[feature]):.2f} is at/above warning {spec["warning"]:.2f}')

    any_predicted_wear = any(p["predicted_wear"] == 1 for p in predictions)
    if spoof_flags or sensor_concern:
        decision = "MONITOR"
        reasons = ["Possible sensor spoof/fault detected; readings must be independently verified."]
    elif any_predicted_wear or maintenance_concern:
        decision = "SCHEDULE_MAINTENANCE"
        reasons = ["Predictive wear signal and/or relevant technician note indicates maintenance concern."]
    elif warning_values:
        decision = "MONITOR"
        reasons = ["At least one measurement is in its warning range."]
    else:
        decision = "SAFE"
        reasons = ["No danger threshold, predicted wear, relevant maintenance note, or spoof indicator found."]

    return {
        "arm_id": arm_id,
        "decision": decision,
        "reasons": reasons + warning_values + spoof_flags + matched_notes,
        "predictions": predictions,
    }

def main() -> None:
    historical_rows = load_csv()
    current_rows = load_csv(CURRENT_PATH)
    notes = load_maintenance_notes()
    model = train_predictor(historical_rows)

    results = [evaluate_arm(arm, current_rows, model, notes) for arm in ARMS]

    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "notice": "Educational synthetic demonstration only; not for controlling real industrial equipment.",
        "thresholds": LIMITS,
        "decisions": results,
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print("ROBOTIC ARM JOINT HEALTH MONITOR")
    print("=" * 36)
    for result in results:
        print(f'\n{result["arm_id"]}: {result["decision"]}')
        for reason in result["reasons"]:
            print(f"  - {reason}")
        if result.get("predictions"):
            print("  Joint predictions:")
            for p in result["predictions"]:
                print(f'    {p["joint"]}: wear={p["predicted_wear"]}, risk_score={p["risk_score"]}')
    print(f"\nSaved detailed output to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
