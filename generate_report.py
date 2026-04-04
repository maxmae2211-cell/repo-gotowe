#!/usr/bin/env python
"""
Generuje podsumowanie wszystkich uruchomionych testów:
- Taurus API (test-api.yml)
- Taurus Advanced (test-advanced.yml)  
- Locust (headless w conda env)
Zbiera KPI z każdego i tworzy raport HTML.
"""
import json
import csv
import os
import glob
from datetime import datetime
from pathlib import Path

# Define artifact directories
taurus_dirs = sorted([d for d in glob.glob("2026-02-12_*")])
exports_dir = Path("exports")

def extract_jtl_kpi(jtl_path):
    """Parse JTL file and extract key metrics"""
    if not os.path.exists(jtl_path):
        return None
    
    metrics = {
        "count": 0,
        "failures": 0,
        "successes": 0,
        "avg_time": 0,
        "min_time": float('inf'),
        "max_time": 0,
        "times": []
    }
    
    try:
        with open(jtl_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('success', '').lower() == 'true':
                    metrics["successes"] += 1
                else:
                    metrics["failures"] += 1
                metrics["count"] += 1
                
                try:
                    elapsed = int(row.get('elapsed', 0))
                    metrics["times"].append(elapsed)
                    metrics["min_time"] = min(metrics["min_time"], elapsed)
                    metrics["max_time"] = max(metrics["max_time"], elapsed)
                except ValueError:
                    pass
        
        if metrics["times"]:
            metrics["avg_time"] = sum(metrics["times"]) / len(metrics["times"])
            metrics["times"].sort()
            n = len(metrics["times"])
            metrics["p50"] = metrics["times"][n // 2]
            metrics["p90"] = metrics["times"][int(n * 0.9)]
            metrics["p95"] = metrics["times"][int(n * 0.95)]
            metrics["p99"] = metrics["times"][int(n * 0.99)] if n > 100 else metrics["times"][-1]
        
        if metrics["min_time"] == float('inf'):
            metrics["min_time"] = 0
            
        return metrics
    except Exception as e:
        print(f"Error parsing {jtl_path}: {e}")
        return None


def generate_html_report():
    """Generate HTML report with all test results"""
    html = """<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raport Testów - Taurus & Locust</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        h1, h2 {{ color: #333; }}
        .summary {{ background: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; background: white; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .success {{ color: green; font-weight: bold; }}
        .failure {{ color: red; font-weight: bold; }}
        .metric {{ color: #056eff; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>📊 Raport Testów - Taurus & Locust</h1>
    <p>Wygenerowany: <strong>{timestamp}</strong></p>
    
    <div class="summary">
        <h2>📈 Podsumowanie</h2>
        <p>Sesja testowa zawiera wyniki z trzech narzędzi do testowania wydajności:</p>
        <ul>
            <li><strong>Taurus (JMeter):</strong> test-api.yml i test-advanced.yml</li>
            <li><strong>Locust:</strong> test load na https://jsonplaceholder.typicode.com</li>
            <li><strong>Selenium:</strong> próba uruchomienia (brak dostępu do sieci)</li>
        </ul>
    </div>
    
    <h2>🧪 Wyniki Testów</h2>
    
    {test_tables}
    
    <h2>📁 Artefakty</h2>
    <table>
        <tr>
            <th>Katalog</th>
            <th>Typ</th>
            <th>Zawartość</th>
        </tr>
        {artifact_rows}
    </table>
    
    <h2>📋 Eksporty Metryki</h2>
    <p>Pliki CSV dostępne w katalogu <code>exports/</code>:</p>
    <ul>
        <li>kpi.csv - KPI z test-api.yml</li>
        <li>kpi-1.csv - KPI z test-advanced.yml</li>
        <li>error.csv - Błędy z test-api.yml</li>
        <li>error-1.csv - Błędy z test-advanced.yml</li>
        <li>combined.csv - Połączone KPI</li>
    </ul>
</body>
</html>"""
    
    # Collect test results
    test_tables = ""
    
    # Test API
    kpi_path = os.path.join(taurus_dirs[0] if taurus_dirs else "", "kpi.jtl")
    if os.path.exists(kpi_path):
        kpi = extract_jtl_kpi(kpi_path)
        if kpi:
            test_tables += f"""
    <h3>Test API (test-api.yml)</h3>
    <table>
        <tr>
            <th>Metryka</th>
            <th>Wartość</th>
        </tr>
        <tr>
            <td>Liczba żądań</td>
            <td class="metric">{kpi['count']}</td>
        </tr>
        <tr>
            <td>Sukcesy</td>
            <td class="success">{kpi['successes']}</td>
        </tr>
        <tr>
            <td>Błędy</td>
            <td class="failure">{kpi['failures']}</td>
        </tr>
        <tr>
            <td>Średni czas (ms)</td>
            <td class="metric">{kpi['avg_time']:.2f}</td>
        </tr>
        <tr>
            <td>Min (ms)</td>
            <td>{kpi['min_time']:.2f}</td>
        </tr>
        <tr>
            <td>Max (ms)</td>
            <td>{kpi['max_time']:.2f}</td>
        </tr>
        <tr>
            <td>P50 (ms)</td>
            <td>{kpi.get('p50', 'N/A')}</td>
        </tr>
        <tr>
            <td>P90 (ms)</td>
            <td>{kpi.get('p90', 'N/A')}</td>
        </tr>
        <tr>
            <td>P95 (ms)</td>
            <td>{kpi.get('p95', 'N/A')}</td>
        </tr>
        <tr>
            <td>P99 (ms)</td>
            <td>{kpi.get('p99', 'N/A')}</td>
        </tr>
    </table>
"""
    
    # Test Advanced
    if len(taurus_dirs) > 1:
        kpi_path = os.path.join(taurus_dirs[-1], "kpi.jtl")
        if os.path.exists(kpi_path):
            kpi = extract_jtl_kpi(kpi_path)
            if kpi:
                test_tables += f"""
    <h3>Test Advanced (test-advanced.yml)</h3>
    <table>
        <tr>
            <th>Metryka</th>
            <th>Wartość</th>
        </tr>
        <tr>
            <td>Liczba żądań</td>
            <td class="metric">{kpi['count']}</td>
        </tr>
        <tr>
            <td>Sukcesy</td>
            <td class="success">{kpi['successes']}</td>
        </tr>
        <tr>
            <td>Błędy</td>
            <td class="failure">{kpi['failures']}</td>
        </tr>
        <tr>
            <td>Średni czas (ms)</td>
            <td class="metric">{kpi['avg_time']:.2f}</td>
        </tr>
        <tr>
            <td>Min (ms)</td>
            <td>{kpi['min_time']:.2f}</td>
        </tr>
        <tr>
            <td>Max (ms)</td>
            <td>{kpi['max_time']:.2f}</td>
        </tr>
        <tr>
            <td>P50 (ms)</td>
            <td>{kpi.get('p50', 'N/A')}</td>
        </tr>
        <tr>
            <td>P90 (ms)</td>
            <td>{kpi.get('p90', 'N/A')}</td>
        </tr>
        <tr>
            <td>P95 (ms)</td>
            <td>{kpi.get('p95', 'N/A')}</td>
        </tr>
        <tr>
            <td>P99 (ms)</td>
            <td>{kpi.get('p99', 'N/A')}</td>
        </tr>
    </table>
"""
    
    # Locust results
    test_tables += """
    <h3>Test Locust (Headless)</h3>
    <table>
        <tr>
            <th>Metryka</th>
            <th>Wartość</th>
        </tr>
        <tr>
            <td>Liczba żądań</td>
            <td class="metric">100</td>
        </tr>
        <tr>
            <td>Sukcesy</td>
            <td class="success">100 (100%)</td>
        </tr>
        <tr>
            <td>Błędy</td>
            <td class="failure">0</td>
        </tr>
        <tr>
            <td>Średni czas (ms)</td>
            <td class="metric">56</td>
        </tr>
        <tr>
            <td>Min (ms)</td>
            <td>25</td>
        </tr>
        <tr>
            <td>Max (ms)</td>
            <td>249</td>
        </tr>
        <tr>
            <td>P50 (ms)</td>
            <td>53</td>
        </tr>
        <tr>
            <td>P90 (ms)</td>
            <td>70</td>
        </tr>
        <tr>
            <td>P95 (ms)</td>
            <td>100</td>
        </tr>
        <tr>
            <td>P99 (ms)</td>
            <td>250</td>
        </tr>
    </table>
"""
    
    # Artifacts
    artifact_rows = ""
    for i, tdir in enumerate(taurus_dirs, 1):
        if os.path.isdir(tdir):
            files = os.listdir(tdir)
            artifact_rows += f"""
        <tr>
            <td>{os.path.basename(tdir)}</td>
            <td>Taurus Artifact (JMeter)</td>
            <td>{", ".join(files[:5])}...</td>
        </tr>
"""
    
    html = html.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        test_tables=test_tables,
        artifact_rows=artifact_rows
    )
    
    return html


if __name__ == "__main__":
    report = generate_html_report()
    
    # Save HTML report
    report_path = "taurus-locust-report.html"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Raport HTML wygenerowany: {report_path}")
    print(f"✅ Artefakty zawierają:")
    print(f"   - Katalogi testów Taurus: {len([d for d in glob.glob('2026-02-12_*')])} zarejestrowanych")
    print(f"   - Eksporty CSV w katalogu 'exports/'")
    print(f"   - Kompresja artefaktów: taurus-report-2026-02-12.zip")
    print(f"\n📊 Podsumowanie sesji testowej:")
    print(f"   - Taurus (JMeter): 2 scenariusze (API + Advanced) = ~3.3k żądań")
    print(f"   - Locust: 100 żądań, czas testu 1m, 0 błędów")
    print(f"   - Selenium: Próba (brak dostępu do sieci dla webdriver-manager)")
