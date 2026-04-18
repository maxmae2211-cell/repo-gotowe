#!/usr/bin/env python3
"""
Generuje podsumowanie wszystkich uruchomionych testów Taurus.
Zbiera KPI z katalogów artefaktów i tworzy raport HTML.
"""
import argparse
import os
import glob
from datetime import datetime
from pathlib import Path

from jtl_metrics import extract_jtl_kpi


def _kpi_table(title: str, kpi: dict) -> str:
    """Returns an HTML fragment with a KPI table for one result set."""
    return f"""
    <h3>{title}</h3>
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
            <td>{kpi['min_time']}</td>
        </tr>
        <tr>
            <td>Max (ms)</td>
            <td>{kpi['max_time']}</td>
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


def generate_html_report(taurus_dirs: list) -> str:
    """Generate HTML report with all test results."""
    html_template = """<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raport Testów - Taurus</title>
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
        .no-data {{ color: #888; font-style: italic; }}
    </style>
</head>
<body>
    <h1>📊 Raport Testów - Taurus</h1>
    <p>Wygenerowany: <strong>{timestamp}</strong></p>

    <div class="summary">
        <h2>📈 Podsumowanie</h2>
        <p>Sesja testowa zawiera wyniki z Taurus (JMeter):</p>
        <ul>
            <li><strong>Taurus (JMeter):</strong> test-api.yml i test-advanced.yml</li>
        </ul>
        <p>Liczba katalogów artefaktów: <strong>{artifact_count}</strong></p>
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

    test_tables = ""

    for i, tdir in enumerate(taurus_dirs):
        kpi_path = Path(tdir) / "kpi.jtl"
        if kpi_path.exists():
            kpi = extract_jtl_kpi(kpi_path)
            if kpi and kpi["count"]:
                label = f"Test #{i + 1} — {os.path.basename(tdir)}"
                test_tables += _kpi_table(label, kpi)

    if not test_tables:
        test_tables = '<p class="no-data">Brak danych testowych — nie znaleziono plików kpi.jtl w katalogach artefaktów.</p>'

    artifact_rows = ""
    for tdir in taurus_dirs:
        if os.path.isdir(tdir):
            files = os.listdir(tdir)
            artifact_rows += f"""
        <tr>
            <td>{os.path.basename(tdir)}</td>
            <td>Taurus Artifact (JMeter)</td>
            <td>{", ".join(files[:5])}{"..." if len(files) > 5 else ""}</td>
        </tr>
"""

    return html_template.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        artifact_count=len(taurus_dirs),
        test_tables=test_tables,
        artifact_rows=artifact_rows,
    )


def parse_args() -> argparse.Namespace:
    default_pattern = f"{datetime.now().year}-*"
    parser = argparse.ArgumentParser(description="Generowanie zbiorczego raportu HTML")
    parser.add_argument(
        "--artifacts-pattern",
        default=default_pattern,
        help=(
            "Wzorzec katalogów artefaktów Taurus "
            f"(domyślnie: {default_pattern})."
        ),
    )
    parser.add_argument(
        "--output",
        default="taurus-locust-report.html",
        help="Ścieżka pliku wyjściowego HTML.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    taurus_dirs = sorted(glob.glob(args.artifacts_pattern))
    report = generate_html_report(taurus_dirs)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ Raport HTML wygenerowany: {args.output}")
    print(f"   - Katalogi testów Taurus: {len(taurus_dirs)} zarejestrowanych")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

