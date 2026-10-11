
import random
import time
import csv

LOG_FILE = "day1_log.csv"


# STEP 1 - Generate simulated sensor data
def generate_sensor_data():
    return {
        "temperature": round(random.uniform(50, 95), 2),
        "pressure": round(random.uniform(80, 150), 2),
        "vibration": round(random.uniform(0.1, 8), 2),
        "current": round(random.uniform(5, 25), 2)
    }


# STEP 2 - Define automation rules
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


# STEP 3 - Evaluate rules according to priority
def evaluate_rules(reading, rules):
    for rule in sorted(rules, key=lambda x: x["priority"]):
        if rule["condition"](reading):
            return rule["name"], rule["action"]

    return "NO_RULE_FIRED", "CONTINUE_NORMAL"


# STEP 4 - Determine machine state
def get_state(action):
    states = {
        "STOP_MACHINE": "STOP",
        "ISSUE_WARNING": "WARNING",
        "REDUCE_LOAD": "REDUCE_LOAD",
        "CONTINUE_NORMAL": "NORMAL"
    }

    return states.get(action, "UNKNOWN")


# STEP 5 - Initialize CSV file
def initialize_log():
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "temperature",
            "pressure",
            "vibration",
            "current",
            "state"
        ])


# STEP 6 - Save sensor readings and state to CSV
def log_decision(reading, state):
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            reading["temperature"],
            reading["pressure"],
            reading["vibration"],
            reading["current"],
            state
        ])


# STEP 7 - Run the automation system
def main():
    print("=" * 55)
    print("     INDUSTRIAL AUTOMATION RULE ENGINE")
    print("=" * 55)

    initialize_log()

    rule_counts = {}
    stop_detected = False
    total_cycles = 500

    for tick in range(1, total_cycles + 1):

        # SENSE
        reading = generate_sensor_data()

        # THINK
        rule_name, action = evaluate_rules(reading, RULES)

        # ACT
        state = get_state(action)

        if state == "STOP":
            stop_detected = True

        rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1

        print(f"\n[Tick {tick:03d}]")
        print(f"SENSE -> {reading}")
        print(f"THINK -> {rule_name}")
        print(f"STATE -> {state}")

        # LOG
        log_decision(reading, state)

        time.sleep(0.2)

    # STEP 8 - Display simulation summary
    print("\n" + "=" * 55)
    print("SIMULATION SUMMARY")
    print("=" * 55)

    print("Total cycles:", total_cycles)
    print("Stop condition detected:", "YES" if stop_detected else "NO")

    print("\nRules triggered:")
    for name, count in sorted(rule_counts.items()):
        print(f"{name}: {count}")

    print(f"\nCSV log saved to: {LOG_FILE}")
    print("Simulation completed!")


# Program entry point
if __name__ == "__main__":
    main()
