"""
Analysis API for the Smart Environment Monitor.
n8n sends each sensor reading here; we return moving average + anomaly status.
Run: python analysis_api.py
"""
import csv
import io
import os
from collections import deque
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # no GUI needed
import matplotlib.pyplot as plt
from flask import Flask, jsonify, request, send_file

app = Flask(__name__)

SENSORS = ["temperature", "humidity", "gas"]
WINDOW = 20          # readings used for moving average / z-score
Z_THRESHOLD = 2.5    # how far from average counts as an anomaly
MIN_READINGS = 5     # need a few readings before judging anomalies

# hard limits (alert even if the z-score looks normal)
LIMITS = {
    "temperature": (10, 40),    # deg C
    "humidity": (20, 80),       # %
    "gas": (0, 400),            # ppm
}

history = {s: deque(maxlen=WINDOW) for s in SENSORS}
LOG_FILE = "readings_log.csv"


def mean_std(values):
    n = len(values)
    avg = sum(values) / n
    var = sum((v - avg) ** 2 for v in values) / n
    return avg, var ** 0.5


def log_reading(row):
    new_file = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["timestamp", *SENSORS, "status"])
        w.writerow(row)


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(force=True)
    result = {}
    anomalies = []

    for s in SENSORS:
        if s not in data:
            continue
        value = float(data[s])
        buf = history[s]

        z = 0.0
        avg = value
        if len(buf) >= MIN_READINGS:
            avg, std = mean_std(buf)
            z = (value - avg) / std if std > 0 else 0.0

        low, high = LIMITS[s]
        out_of_range = value < low or value > high
        spike = abs(z) > Z_THRESHOLD

        if out_of_range or spike:
            anomalies.append(s)

        result[s] = {
            "value": value,
            "moving_avg": round(avg, 2),
            "z_score": round(z, 2),
            "out_of_range": out_of_range,
            "spike": spike,
        }
        buf.append(value)

    status = "ANOMALY" if anomalies else "OK"
    log_reading([
        datetime.now().isoformat(timespec="seconds"),
        *[data.get(s, "") for s in SENSORS],
        status,
    ])

    return jsonify({
        "status": status,
        "anomaly": bool(anomalies),
        "anomalous_sensors": anomalies,
        "details": result,
        "message": (
            f"ALERT: {', '.join(anomalies)} abnormal! "
            + ", ".join(f"{s}={result[s]['value']}" for s in anomalies)
            if anomalies else "All readings normal"
        ),
    })


@app.route("/report", methods=["GET"])
def report():
    """Returns a PNG chart of all logged readings (use in the daily n8n report)."""
    if not os.path.exists(LOG_FILE):
        return jsonify({"error": "no data yet"}), 404

    times, cols = [], {s: [] for s in SENSORS}
    with open(LOG_FILE) as f:
        for row in csv.DictReader(f):
            times.append(datetime.fromisoformat(row["timestamp"]))
            for s in SENSORS:
                cols[s].append(float(row[s]))

    fig, axes = plt.subplots(len(SENSORS), 1, figsize=(9, 8), sharex=True)
    for ax, s in zip(axes, SENSORS):
        ax.plot(times, cols[s], linewidth=1)
        low, high = LIMITS[s]
        ax.axhline(high, color="red", linestyle="--", linewidth=0.8)
        ax.axhline(low, color="red", linestyle="--", linewidth=0.8)
        ax.set_ylabel(s)
        ax.grid(alpha=0.3)
    axes[0].set_title("Environment Monitor Report")
    fig.autofmt_xdate()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/health")
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
