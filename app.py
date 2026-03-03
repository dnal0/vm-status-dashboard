from flask import Flask, render_template_string
import psutil
import datetime

history = {
    'cpu': [],
    'ram': [],
    'disk': [],
    'labels': []  # timestamps
}
MAX_POINTS = 1200

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>VM Monitor • Live</title>
    <meta http-equiv="refresh" content="7">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            color: #e6edf3;
            min-height: 100vh;
            padding: 2.5rem 1.5rem;
            font-family: system-ui, -apple-system, sans-serif;
        }
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(0,0,0,0.4);
        }
        .card-header {
            background: linear-gradient(to right, #21262d, #161b22);
            border-bottom: 1px solid #30363d;
            padding: 1rem 1.25rem;
        }
        .metric-value {
            font-size: 2.4rem;
            font-weight: 700;
            line-height: 1;
        }
        .progress {
            height: 10px;
            background: #21262d;
            border-radius: 5px;
        }
        .progress-bar {
            transition: width 0.8s ease;
        }
        .chart-container {
            position: relative;
            height: 180px;
            width: 100%;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="text-center mb-5">
            <h1 class="display-5 fw-bold text-success mb-1">
                <i class="bi bi-cpu me-2"></i>VM Monitor
            </h1>
            <p class="text-muted">Live system overview • Updated every 7 seconds</p>
        </header>

        <div class="row g-4">
            <!-- System Info -->
            <div class="col-lg-4">
                <div class="card h-100">
                    <div class="card-header d-flex align-items-center">
                        <i class="bi bi-clock-history fs-4 me-2 text-primary"></i>
                        <h5 class="mb-0">System</h5>
                    </div>
                    <div class="card-body">
                        <p class="mb-2"><strong>Current:</strong> {{ now }}</p>
                        <p><strong>Uptime:</strong> {{ uptime }}</p>
                    </div>
                </div>
            </div>

            <!-- CPU with Chart -->
            <div class="col-lg-8">
                <div class="card h-100">
                    <div class="card-header d-flex align-items-center">
                        <i class="bi bi-cpu fs-4 me-2 text-success"></i>
                        <h5 class="mb-0">CPU Usage</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <div class="metric-value text-success">{{ cpu }}%</div>
                            <div class="progress w-50">
                                <div class="progress-bar bg-success" role="progressbar" style="width: {{ cpu }}%"></div>
                            </div>
                        </div>
                        <div class="chart-container">
                            <canvas id="cpuChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- RAM with Chart -->
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header d-flex align-items-center">
                        <i class="bi bi-memory fs-4 me-2 text-info"></i>
                        <h5 class="mb-0">RAM Usage</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <div>
                                <div class="metric-value text-info">{{ ram }} GB</div>
                                <small class="text-muted">{{ ram_percent }}%</small>
                            </div>
                            <div class="progress w-50">
                                <div class="progress-bar bg-info" role="progressbar" style="width: {{ ram_percent }}%"></div>
                            </div>
                        </div>
                        <div class="chart-container">
                            <canvas id="ramChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Disk with Chart -->
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header d-flex align-items-center">
                        <i class="bi bi-hdd fs-4 me-2 text-warning"></i>
                        <h5 class="mb-0">Disk Usage</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <div>
                                <div class="metric-value text-warning">{{ disk }} GB</div>
                                <small class="text-muted">{{ disk_percent }}%</small>
                            </div>
                            <div class="progress w-50">
                                <div class="progress-bar bg-warning text-dark" role="progressbar" style="width: {{ disk_percent }}%"></div>
                            </div>
                        </div>
                        <div class="chart-container">
                            <canvas id="diskChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="text-center mt-5 text-muted small">
            Powered by Flask • psutil • Chart.js • Ubuntu Server • Running 24/7
        </footer>
    </div>

    <script>
        // CPU Chart
        const cpuCtx = document.getElementById('cpuChart').getContext('2d');
        new Chart(cpuCtx, {
            type: 'line',
            data: {
                labels: {{ history.labels | tojson }},
                datasets: [{
                    label: 'CPU %',
                    data: {{ history.cpu | tojson }},
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.2)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { min: 0, max: 100 } }
            }
        });

        // RAM Chart
        const ramCtx = document.getElementById('ramChart').getContext('2d');
        new Chart(ramCtx, {
            type: 'line',
            data: {
                labels: {{ history.labels | tojson }},
                datasets: [{
                    label: 'RAM %',
                    data: {{ history.ram | tojson }},
                    borderColor: '#0dcaf0',
                    backgroundColor: 'rgba(13, 202, 240, 0.2)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { min: 0, max: 100 } }
            }
        });

        // Disk Chart
        const diskCtx = document.getElementById('diskChart').getContext('2d');
        new Chart(diskCtx, {
            type: 'line',
            data: {
                labels: {{ history.labels | tojson }},
                datasets: [{
                    label: 'Disk %',
                    data: {{ history.disk | tojson }},
                    borderColor: '#ffc107',
                    backgroundColor: 'rgba(255, 193, 7, 0.2)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { min: 0, max: 100 } }
            }
        });
    </script>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
</body>
</html>
"""


@app.route("/")
def status():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
    cpu = psutil.cpu_percent()
    ram = round(psutil.virtual_memory().used / (1024**3), 1)
    ram_percent = psutil.virtual_memory().percent
    disk = round(psutil.disk_usage('/').used / (1024**3), 1)
    disk_percent = psutil.disk_usage('/').percent
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    history['labels'].append(now_str)
    history['cpu'].append(cpu)
    history['ram'].append(ram_percent)
    history['disk'].append(disk_percent)

    if len(history['labels']) > MAX_POINTS:
        history['labels'] = history['labels'][-MAX_POINTS:]
        history['cpu'] = history['cpu'][-MAX_POINTS:]
        history['ram'] = history['ram'][-MAX_POINTS:]
        history['disk'] = history['disk'][-MAX_POINTS:]
   

    print(f"Points collected: {len(history['labels'])}, Last CPU: {history['cpu'][-1] if history['cpu'] else 'empty'}")

    return render_template_string(HTML,
    now=now,
    uptime=str(uptime).split('.')[0],
    cpu=cpu,
    ram=ram,
    ram_percent=ram_percent,
    disk=disk,
    disk_percent=disk_percent,
    history=history
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
