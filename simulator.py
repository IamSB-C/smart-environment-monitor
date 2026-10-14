"""
Fake sensor simulator. Sends temperature / humidity / gas readings to n8n webhook.
Run: python simulator.py
"""
import math
import random
import time

import requests

# n8n webhook URL (use the TEST url while building, PRODUCTION url once the workflow is active)
WEBHOOK_URL = "http://localhost:5678/webhook/sensor"
INTERVAL = 3          # seconds between readings
SPIKE_CHANCE = 0.06   # ~6% of readings will be abnormal


def make_reading(t):
    # slow natural drift (sine wave) + small noise
    temp = 28 + 3 * math.sin(t / 60) + random.gauss(0, 0.3)
    hum = 55 + 8 * math.sin(t / 90 + 1) + random.gauss(0, 1)
    gas = 150 + 30 * math.sin(t / 45) + random.gauss(0, 5)

    # random spike on one sensor
    if random.random() < SPIKE_CHANCE:
        which = random.choice(["temp", "hum", "gas"])
        if which == "temp":
            temp += random.uniform(12, 20)
        elif which == "hum":
            hum += random.uniform(30, 40)
        else:
            gas += random.uniform(300, 500)
        print(f"  >> injected spike on {which}")

    return {
        "temperature": round(temp, 2),
        "humidity": round(hum, 2),
        "gas": round(gas, 2),
    }


def main():
    start = time.time()
    print(f"Sending to {WEBHOOK_URL} every {INTERVAL}s (Ctrl+C to stop)")
    while True:
        reading = make_reading(time.time() - start)
        try:
            r = requests.post(WEBHOOK_URL, json=reading, timeout=10)
            print(f"{reading} -> {r.status_code}")
        except requests.RequestException as e:
            print(f"send failed: {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
