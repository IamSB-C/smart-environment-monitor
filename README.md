# Smart Environment Monitor

Automated environment monitoring built with **n8n** and **Python**. A simulated sensor node sends temperature, humidity and gas readings to an n8n workflow, a Python API detects anomalies, and spikes trigger instant **Telegram alerts**. A second workflow sends a **daily chart report**.

No hardware needed. The simulator can later be replaced by a real ESP32/Arduino posting to the same webhook.

## Features

- Simulated multi-sensor data (temperature, humidity, gas) with random fault spikes
- n8n workflow: webhook → analysis → conditional alert
- Anomaly detection using a **moving-window z-score** plus **fixed safety limits**
- Real-time Telegram alerts
- Daily chart report (Matplotlib) delivered to Telegram
- Every reading logged to a CSV file

## Architecture

```
simulator.py --POST--> [n8n Webhook] --> [HTTP Request: Flask /analyze]
                                                  |
                                           [IF: anomaly?]
                                              /        \
                                  [Telegram alert]   (no action)

[Schedule Trigger, 8 PM] --> [HTTP Request: /report] --> [Telegram: Send Photo]
```

## Tech Stack

Python 3, Flask, Matplotlib, n8n (Docker), Telegram Bot API

## Project Structure

```
smart-environment-monitor/
├── analysis_api.py        # Flask API: /analyze, /report, /health
├── simulator.py           # Fake sensor data generator
├── requirements.txt
├── workflows/             # Exported n8n workflows (import these)
├── screenshots/           # Workflow, alert and chart screenshots
├── Project_Report.md      # Full project report
└── README.md
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the analysis API

```bash
python analysis_api.py
```

Check it at `http://localhost:5000/health`. It should return `{"ok": true}`.

### 3. Set up the Telegram bot

1. Message **@BotFather** on Telegram, send `/newbot`, and copy the token.
2. Message **@userinfobot** to get your Chat ID.
3. Open your new bot and press **Start**.

### 4. Import the n8n workflows

1. In n8n, go to **Workflows → Import from file** and import the files from `workflows/`.
2. Create a **Telegram credential** with your bot token, and select it in the Telegram nodes.
3. Set your **Chat ID** in the Telegram nodes.
4. In the HTTP Request nodes, check the API URL:
   - n8n in Docker: `http://host.docker.internal:5000`
   - n8n installed locally: `http://localhost:5000`
5. **Publish** both workflows.

### 5. Run the simulator

```bash
python simulator.py
```

Each line should end with `-> 200`. Watch runs in n8n's **Executions** tab, and expect Telegram alerts whenever a spike is injected.

## How Anomaly Detection Works

Each reading is checked in two ways:

1. **Z-score:** compared with the last 20 readings of that sensor. If `|z| > 2.5`, it is flagged as a spike.
2. **Safety limits:** a fixed range per sensor.

| Sensor | Min | Max |
|---|---|---|
| Temperature | 10 °C | 40 °C |
| Humidity | 20 % | 80 % |
| Gas | 0 ppm | 400 ppm |

If either check fails, the API returns `status: ANOMALY` and n8n sends the alert.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/analyze` | Takes `{temperature, humidity, gas}`, returns status, moving averages and z-scores |
| GET | `/report` | Returns a PNG chart of all logged readings |
| GET | `/health` | Health check |

Example request:

```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"temperature": 80, "humidity": 55, "gas": 150}'
```

## Screenshots

| n8n workflow | Telegram alerts | Daily report |
|---|---|---|
| ![workflow](screenshots/workflow.png) | ![alerts](screenshots/alerts.png) | ![report](screenshots/report.png) |

## Configuration

Settings live at the top of the Python files:

- `simulator.py`: `WEBHOOK_URL`, `INTERVAL`, `SPIKE_CHANCE`
- `analysis_api.py`: `WINDOW`, `Z_THRESHOLD`, `MIN_READINGS`, `LIMITS`

## Limitations

- Data is simulated, not from physical sensors
- Runs only while the laptop, Docker and the Flask API are on
- Flask development server, not production-ready

## Future Work

- Real ESP32 + DHT22 / MQ-2 sensors
- Isolation Forest anomaly detection
- MQTT instead of HTTP
- Live dashboard (Streamlit/Grafana)
- Buzzer/fan control for a closed-loop system

