# VM Status Dashboard

A simple, live system monitoring dashboard running on an Ubuntu Server VM.

## Features
- Real-time CPU, RAM, and Disk usage
- Progress bars + line charts with history (up to ~140 minutes)
- Dark modern theme (Bootstrap 5 + Icons)
- Auto-refresh every 7 seconds
- Runs permanently as a systemd service (survives reboots)

## Technologies
- Flask (web framework)
- psutil (system metrics)
- Chart.js (live charts)
- Bootstrap 5 (styling)

## How to run locally
1. Clone the repo
2. `cd vm-status-dashboard`
3. `python3 -m venv venv && source venv/bin/activate`
4. `pip install flask psutil`
5. `python3 app.py`

## Screenshots



Built as my first real Linux server project – March 2026.
