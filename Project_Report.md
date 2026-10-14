# Smart Environment Monitor: Automated Anomaly Detection and Alerting using n8n and Python



---

## 1. Abstract

This project builds an automated environment monitoring system that collects sensor readings (temperature, humidity and gas concentration), analyses them for abnormal behaviour, and instantly alerts the user on Telegram. A Python simulator generates realistic sensor data, an n8n workflow orchestrates the data flow, and a Python (Flask) analysis service detects anomalies using a moving average, z-score test and fixed safety limits. A second workflow sends a daily chart report. The system needs no hardware, and the simulator can later be replaced with a real ESP32 or Arduino without changing the workflow.

## 2. Problem Statement

Environmental parameters such as temperature, humidity and gas levels need continuous monitoring in places like server rooms, labs, workshops and storage areas. Manual monitoring is slow and unreliable, and abnormal conditions (overheating, gas leaks, excess moisture) can go unnoticed until damage occurs. An automated system that detects abnormal readings and notifies the user immediately solves this problem.

## 3. Objectives

1. Simulate a multi-sensor IoT node that sends data periodically.
2. Receive and route the data automatically using n8n.
3. Detect anomalies using statistical methods and safety thresholds.
4. Send real-time alerts to the user's phone via Telegram.
5. Log all readings and generate a daily visual report.

## 4. Tools and Technologies

| Tool | Purpose |
|---|---|
| Python 3 | Sensor simulation and analysis logic |
| Flask | REST API for the analysis service |
| Matplotlib | Chart generation for the report |
| n8n (Docker) | Workflow automation and orchestration |
| Telegram Bot API | Alert and report delivery |
| CSV file | Persistent data log |
| VS Code | Development environment |

## 5. System Architecture

```
simulator.py --POST--> [n8n Webhook] --> [HTTP Request: Flask /analyze]
                                                  |
                                           [IF: anomaly = true?]
                                              /          \
                                  [Telegram alert]     (no action)

[Schedule Trigger, 8 PM] --> [HTTP Request: Flask /report] --> [Telegram: Send Photo]
```

### 5.1 Components

**Sensor simulator (`simulator.py`)**
Generates a reading every 3 seconds. Each value follows a slow sine-wave drift with Gaussian noise to mimic real sensors (temperature around 28 °C, humidity around 55 %, gas around 150 ppm). With about 6 % probability a reading is given a large random spike on one sensor, to imitate faults such as a heat event, a humidity surge or a gas leak. Readings are sent as JSON to the n8n webhook.

**n8n main workflow**
1. **Webhook node** receives the sensor data (POST, path `sensor`).
2. **HTTP Request node** forwards the readings to the Flask `/analyze` endpoint.
3. **IF node** checks whether the API flagged an anomaly.
4. **Telegram node** (true branch) sends an alert message to the user.

**Analysis API (`analysis_api.py`)**
Keeps a sliding window of the last 20 readings per sensor and returns the status, moving average, z-score and a human-readable message. Every reading is also appended to `readings_log.csv`.

**Daily report workflow**
A Schedule Trigger fires at 8 PM, fetches the chart from the `/report` endpoint and sends it to Telegram as a photo.

## 6. Anomaly Detection Method

Two complementary checks are applied to every sensor value.

### 6.1 Statistical check (z-score)

For each sensor, the mean (μ) and standard deviation (σ) of the last 20 readings are calculated. The z-score of a new reading x is:

```
z = (x - μ) / σ
```

A reading is flagged as a **spike** if |z| > 2.5. This catches sudden changes relative to recent behaviour, even when the value is still inside the safe range. The check starts only after 5 readings have been collected, so the baseline is meaningful.

### 6.2 Safety-limit check

Fixed limits catch values that are dangerous in absolute terms, regardless of history:

| Sensor | Lower limit | Upper limit |
|---|---|---|
| Temperature | 10 °C | 40 °C |
| Humidity | 20 % | 80 % |
| Gas | 0 ppm | 400 ppm |

A reading outside its range is flagged as **out of range**.

### 6.3 Decision

If either check fails for any sensor, the API returns `status = ANOMALY`, lists the affected sensors, and includes an alert message such as `ALERT: gas abnormal! gas=493.21`. Otherwise it returns `status = OK`.

Using both checks makes the system robust. The z-score adapts to the normal pattern, while the fixed limits guarantee an alert for dangerous values even if the baseline itself has drifted.

## 7. Implementation Summary

1. Wrote and tested the Flask API locally using manual test requests.
2. Created the n8n workflow and tested each node separately in test mode.
3. Connected the Telegram bot (created through BotFather) using a credential in n8n.
4. Since n8n runs in Docker, the API is reached at `host.docker.internal:5000`.
5. Published the workflow and switched the simulator from the test webhook URL to the production URL, so the whole pipeline runs automatically.
6. Built the daily report workflow and published it.

## 8. Results

- The pipeline ran continuously, with the simulator posting every 3 seconds and each reading producing a successful n8n execution.
- Injected spikes on temperature, humidity and gas were detected and sent to Telegram as alerts (for example `humidity=98.45`, `gas=493.21`, `temperature=50.43`).
- Normal readings produced no alerts.
- Every reading was logged to `readings_log.csv`.
- The daily report delivered a three-panel chart (temperature, humidity, gas) with the safety limits marked as red dashed lines.

> **Add screenshots here:**
> 1. Main n8n workflow (Editor view)
> 2. n8n Executions list showing successful runs
> 3. Telegram alert messages
> 4. Daily report chart in Telegram
> 5. Terminal showing the simulator output (`-> 200`)

## 9. Limitations

- Data is simulated, not measured by physical sensors.
- Anomaly detection depends on the 20-reading window and fixed limits, so it may need tuning for real environments.
- The system works only while the laptop, Docker and the Flask API are running.
- The Flask server is a development server and is not intended for production use.
- The analysis history is stored in memory and resets when the API restarts (the CSV log is kept).

## 10. Future Scope

1. Replace the simulator with a real **ESP32/Arduino** using a DHT11/DHT22 and an MQ-series gas sensor, posting to the same webhook.
2. Use machine-learning detection such as **Isolation Forest** instead of, or alongside, the z-score.
3. Use **MQTT** instead of HTTP for more efficient IoT communication.
4. Add a live dashboard using Streamlit or Grafana.
5. Log to Google Sheets or a database for long-term storage.
6. Add actuator control (for example turning on a fan or buzzer when gas is high), which would make it a closed-loop mechatronic system.
7. Deploy the API and n8n on a cloud server so the system runs 24/7.

## 11. Conclusion

The project shows a complete, working IoT-style monitoring pipeline built with low-code automation (n8n) and Python. It detects abnormal sensor behaviour using both statistical and rule-based methods, notifies the user in real time, and produces automated reports. Because the data source is isolated behind a simple webhook, the same system can be moved to real hardware with no changes to the workflow, making it a practical base for further mechatronics and IoT projects.

## 12. References

1. n8n documentation: https://docs.n8n.io
2. Flask documentation: https://flask.palletsprojects.com
3. Telegram Bot API: https://core.telegram.org/bots/api
4. Matplotlib documentation: https://matplotlib.org
