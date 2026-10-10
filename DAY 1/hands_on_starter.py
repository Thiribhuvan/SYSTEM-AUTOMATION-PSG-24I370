
import random
import time
import json
from datetime import datetime

LOG_FILE = "day1_log.txt"
# ---------------------------------------------------------------------------
# STEP 1 — Generate simulated sensor data
# ---------------------------------------------------------------------------
def generate_sensor_data():
    return {
        "temperature": round(random.uniform(50, 95), 2),
        "pressure": round(random.uniform(80, 150), 2),
        "vibration": round(random.uniform(0.1, 8), 2),
        "current": round(random.uniform(5, 25), 2)
    }
# STRETCH GOAL (after the 8 steps below all work): real sensors aren't
# perfectly clean. Try making one field randomly return None (a
# dropout) or spike far outside its normal range every so often, then
 # update evaluate_rules() so a dropout doesn't crash your engine.

# ---------------------------------------------------------------------------
# STEP 2 — Write your first automation rules
# STEP 7 — Add a rule of your own (add another dict to this list)
# STEP 8 — Add one priority rule (lower "priority" number checked first)
# ---------------------------------------------------------------------------
RULES = [
    {
        "name": "CRITICAL_TEMPERATURE",
        "priority": 1,
        "condition": lambda r: r["temperature"] >= 90,
        "action": "STOP_MACHINE"
    },
    {
        "name": "CRITICAL_PRESSURE",
        "priority": 2,
        "condition": lambda r: r["pressure"] >= 145,
        "action": "STOP_MACHINE"
    },
    {
        "name": "HIGH_VIBRATION",
        "priority": 3,
        "condition": lambda r: r["vibration"] >= 7,
        "action": "ISSUE_WARNING"
    },
    {
        "name": "HIGH_CURRENT",
        "priority": 4,
        "condition": lambda r: r["current"] >= 23,
        "action": "STOP_MACHINE"
    },
    {
        "name": "HIGH_TEMPERATURE",
        "priority": 5,
        "condition": lambda r: r["temperature"] >= 80,
        "action": "REDUCE_LOAD"
    },
    {
        "name": "HIGH_PRESSURE",
        "priority": 6,
        "condition": lambda r: r["pressure"] >= 135,
        "action": "REDUCE_LOAD"
    },
    {
        "name": "NORMAL_OPERATION",
        "priority": 99,
        "condition": lambda r: True,
        "action": "CONTINUE_NORMAL"
    }
]


# ---------------------------------------------------------------------------
# STEP 3 — Detect machine state from the rules
# ---------------------------------------------------------------------------
def evaluate_rules(reading, rules):
    for rule in sorted(rules, key=lambda x: x["priority"]):
        if rule["condition"](reading):
            return rule["name"], rule["action"]

    return "NO_RULE_FIRED", "CONTINUE_NORMAL"


# ---------------------------------------------------------------------------
# STEP 4 — Trigger an action when a rule fires
# ---------------------------------------------------------------------------
def take_action(action):
    actions = {
        "STOP_MACHINE":
            "STOP MACHINE! Critical condition detected.",
        "ISSUE_WARNING":
            "WARNING! High vibration detected.",
        "REDUCE_LOAD":
            "Reduce machine load and monitor sensors.",
        "CONTINUE_NORMAL":
            "Machine operating normally."
    }

    return actions.get(action, "Unknown action")

# ---------------------------------------------------------------------------
# STEP 5 — Log every decision made
# ---------------------------------------------------------------------------
def log_decision(reading, rule_name, action):
    record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "reading": reading,
        "rule": rule_name,
        "action": action
    }

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# STEP 6 — Add a second sensor to the system
# TODO: add e.g. "current" to generate_sensor_data(), then use it in a rule
# ---------------------------------------------------------------------------
def main():
    print("=" * 55)
    print("     INDUSTRIAL AUTOMATION RULE ENGINE")
    print("=" * 55)

    rule_counts = {}
    stop_detected = False

    for tick in range(1, 11):
        # SENSE
        reading = generate_sensor_data()

        # THINK
        rule_name, action = evaluate_rules(reading, RULES)

        # ACT
        outcome = take_action(action)

        if action == "STOP_MACHINE":
            stop_detected = True

        rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1

        print(f"\n[Tick {tick:02d}]")
        print(f"SENSE -> {reading}")
        print(f"THINK -> {rule_name}")
        print(f"ACT   -> {outcome}")

        # LOG
        log_decision(reading, rule_name, action)

        time.sleep(0.2)

    print("\n" + "=" * 55)
    print("SIMULATION SUMMARY")
    print("=" * 55)
    print("Total cycles:", 10)
    print("Stop condition detected:", "YES" if stop_detected else "NO")

    print("\nRules triggered:")
    for name, count in sorted(rule_counts.items()):
        print(f"{name}: {count}")

    print(f"\nLog saved to: {LOG_FILE}")
    print("Simulation completed!")


if __name__ == "__main__":
    main()
