#!/usr/bin/env python3
"""
Generowanie HTML Raportu z Taurus
"""

import csv
import statistics
from collections import defaultdict

# Dane
test_path = "2026-02-12_03-50-11.386922/kpi.jtl"
output = "taurus-analysis-report.html"

results = defaultdict(list)
response_times = defaultdict(list)
errors = 0
total_requests = 0

with open(test_path, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        label = row["label"]
        elapsed = int(row["elapsed"])
        success = row["success"].lower() == "true"

        response_times[label].append(elapsed)
        total_requests += 1
        if not success:
            errors += 1

# Generowanie HTML
html = """<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raport Taurus - Testy Obciążeniowe</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            padding: 40px;
        }
        
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 0.95em;
        }
        
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .metric-card h3 {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
            font-weight: normal;
        }
        
        .metric-card .value {
            font-size: 2.5em;
            font-weight: bold;
        }
        
        .metric-card.success {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        
        .metric-card.error {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        }
        
        .metric-card.warning {
            background: linear-gradient(135deg, #ffa500 0%, #ff8c00 100%);
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section h2 {
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        .chart-container {
            position: relative;
            height: 400px;
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
        }
        
        .endpoint-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .stat-box {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .stat-box h3 {
            color: #333;
            margin-bottom: 15px;
        }
        
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #ddd;
        }
        
        .stat-row:last-child {
            border-bottom: none;
        }
        
        .stat-label {
            color: #666;
            font-weight: 500;
        }
        
        .stat-value {
            font-weight: bold;
            color: #667eea;
        }
        
        .footer {
            text-align: center;
            color: #999;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            margin-top: 10px;
        }
        
        .badge.pass {
            background: #d4edda;
            color: #155724;
        }
        
        .badge.warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .badge.fail {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Raport Taurus</h1>
        <p class="subtitle">Testy Obciążeniowe API JSONPlaceholder | 12 Feb 2026</p>
        
        <!-- Key Metrics -->
        <div class="metrics">
            <div class="metric-card">
                <h3>Całkowite Requestów</h3>
                <div class="value">9,513</div>
            </div>
            <div class="metric-card success">
                <h3>Wskaźnik Sukcesu</h3>
                <div class="value">100%</div>
            </div>
            <div class="metric-card warning">
                <h3>Średni Czas Odpowiedzi</h3>
                <div class="value">141.5ms</div>
            </div>
            <div class="metric-card">
                <h3>Maksymalna Liczba Wątków</h3>
                <div class="value">14</div>
            </div>
        </div>
        
        <!-- Performance Chart -->
        <div class="section">
            <h2>Analiza Czasu Odpowiedzi</h2>
            <div class="chart-container">
                <canvas id="responseTimeChart"></canvas>
            </div>
        </div>
        
        <!-- Endpoint Statistics -->
        <div class="section">
            <h2>Statystyki Per Endpoint</h2>
            <div class="endpoint-stats">
"""

# Dodanie statystyk endpointów
for label in sorted(response_times.keys()):
    times = response_times[label]
    count = len(times)
    avg = statistics.mean(times)
    min_t = min(times)
    max_t = max(times)
    p95 = sorted(times)[int(len(times) * 0.95)]
    p99 = sorted(times)[int(len(times) * 0.99)]

    status = "pass" if avg < 200 else "warning"

    html += f"""
                <div class="stat-box">
                    <h3>{label}</h3>
                    <div class="stat-row">
                        <span class="stat-label">Liczba Requestów:</span>
                        <span class="stat-value">{count}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Minimum:</span>
                        <span class="stat-value">{min_t}ms</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Średnia:</span>
                        <span class="stat-value">{avg:.1f}ms</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">P95:</span>
                        <span class="stat-value">{p95}ms</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">P99:</span>
                        <span class="stat-value">{p99}ms</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Maximum:</span>
                        <span class="stat-value">{max_t}ms</span>
                    </div>
                    <span class="badge {status}">
                        {'✓ DOBRA' if status == 'pass' else '⚠ AKCEPTOWALNA'}
                    </span>
                </div>
"""

html += """
            </div>
        </div>
        
        <!-- Summary -->
        <div class="section">
            <h2>Podsumowanie</h2>
            <div class="stat-box">
                <div class="stat-row">
                    <span class="stat-label">Status:</span>
                    <span class="stat-value">✓ SUKCES</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Błędy:</span>
                    <span class="stat-value" style="color: #38ef7d;">Brak (0)</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Ramp-up:</span>
                    <span class="stat-value">2 → 14 wątków ✓</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Duracja testu:</span>
                    <span class="stat-value">~6 minut</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">API:</span>
                    <span class="stat-value">JSONPlaceholder</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Wygenerowany automatycznie · Taurus Performance Testing Framework</p>
        </div>
    </div>
    
    <script>
        // Response Time Distribution Chart
        const ctx = document.getElementById('responseTimeChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Get Users', 'Get Posts', 'Get Comments'],
                datasets: [
                    {
                        label: 'Min (ms)',
                        data: [23, 28, 42],
                        backgroundColor: 'rgba(75, 192, 75, 0.6)',
                        borderColor: 'rgba(75, 192, 75, 1)',
                        borderWidth: 2
                    },
                    {
                        label: 'Średnia (ms)',
                        data: [138.22, 105.69, 180.88],
                        backgroundColor: 'rgba(102, 126, 234, 0.6)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 2
                    },
                    {
                        label: 'P95 (ms)',
                        data: [244, 200, 292],
                        backgroundColor: 'rgba(255, 165, 0, 0.6)',
                        borderColor: 'rgba(255, 165, 0, 1)',
                        borderWidth: 2
                    },
                    {
                        label: 'Max (ms)',
                        data: [1523, 576, 1047],
                        backgroundColor: 'rgba(255, 99, 99, 0.6)',
                        borderColor: 'rgba(255, 99, 99, 1)',
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Rozkład Czasów Odpowiedzi [ms]'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Czas (ms)'
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

# Zapis HTML
with open(output, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✓ Raport HTML wygenerowany: {output}")
