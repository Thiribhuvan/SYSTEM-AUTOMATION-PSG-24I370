# Robotic Arm Joint Health Monitoring System
**Course:** 23IF02 — System Automation Bonus Challenge

## Files
- `main.py` — full pipeline: deterministic emergency stop, dependency-free predictive wear classifier, maintenance-note scanning, spoof/fault checks, and final arm decision.
- `historical_readings.csv` — 72 synthetic labeled historical readings (wear_label 0 = normal, 1 = wear risk).
- `current_readings.csv` — 18 current snapshot readings (three joints for each of six arms), used for final decisions.
- `maintenance_log.txt` — 12 sample notes including relevant maintenance signals, sensor issues, and irrelevant notes.
- `arm_decisions.json` — generated detailed decisions after running the code.

## Requirements
Python 3.9+; no third-party packages required.

## Run
1. Extract the folder or keep all files together.
2. Open a terminal in this folder.
3. Run:
   ```bash
   python main.py
   ```
4. Review terminal output and `arm_decisions.json`.

## Decision priority
1. `EMERGENCY_STOP`: any single current reading reaches a danger threshold. This rule is deterministic and runs before the predictor.
2. `MONITOR`: sensor spoof/fault indicators or warning-range readings need verification.
3. `SCHEDULE_MAINTENANCE`: model predicts wear or technician notes indicate a maintenance concern.
4. `SAFE`: none of the above is present.

## Illustrative thresholds
- Torque: warning 70 Nm; danger 100 Nm
- Temperature: warning 70 °C; danger 90 °C
- Vibration: warning 5 mm/s; danger 9 mm/s

These are invented teaching thresholds for synthetic data, not certified industrial limits.

## Synthetic data and current demonstration
The historical CSV contains 72 labeled examples for training. The separate current snapshot contains 18 rows: one row per joint for each of six arms. Labels are not used in final decisions. This keeps training data separate from current readings and the project dependency-free.

## Spoof defense: scope and limitations
The defense flags suspicious maintenance notes, high torque that conflicts with low temperature and vibration, and high torque values that remain nearly unchanged across five recent samples for the same arm/joint. It can catch simple or obvious inconsistencies. It may miss plausible spoofed values, coordinated spoofing of multiple sensors, or attacks that avoid the checks. Real deployment needs authenticated sensor communication, signed messages, independent safety-rated monitoring, secure logging, and validation against real operational data.

## Important safety note
This is a classroom simulation only. Do not connect this script to a real robot or use these thresholds to make real safety decisions. Real equipment needs manufacturer-approved limits, risk assessment, independent safety-rated controllers, and validation by qualified engineers.
