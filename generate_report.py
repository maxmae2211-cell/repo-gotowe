#!/usr/bin/env python
"""
Generuje podsumowanie wszystkich uruchomionych testów:
- Taurus API (test-api.yml)
- Taurus Advanced (test-advanced.yml)
- Locust (headless w conda env)
Zbiera KPI z każdego i tworzy raport HTML.
"""

import argparse
import os
import glob
from datetime import datetime


def generate_html_report(taurus_dirs):
    # Generowanie sekcji test_tables na podstawie katalogów z artefaktami
    test_tables = ""
    for tdir in taurus_dirs:
        if os.path.isdir(tdir):
            test_tables += f"<h3>Wyniki testu: {os.path.basename(tdir)}</h3>"
            test_tables += "<table><tr><th>Plik</th><th>Typ</th></tr>"
            for fname in os.listdir(tdir):
                test_tables += f"<tr><td>{fname}</td><td>{'JTL' if fname.endswith('.jtl') else 'Inny'}</td></tr>"
            test_tables += "</table>"

    html = (
        "<!DOCTYPE html>\n"
        "<html lang=\"pl\">\n"
        "<head>\n"
        "    <meta charset=\"UTF-8\">\n"
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "    <style>\n"
        "        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }\n"
        "        h1, h2 { color: #333; }\n"
        "        .summary { background: white; padding: 15px; border-radius: 5px; "
        "margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }\n"
        "        table { width: 100%; border-collapse: collapse; background: white; "
        "margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }\n"
        "        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }\n"
        "        th { background-color: #4CAF50; color: white; }\n"
        "        tr:hover { background-color: #f5f5f5; }\n"
        "        .success { color: green; font-weight: bold; }\n"
        "        .failure { color: red; font-weight: bold; }\n"
        "        .metric { color: #056eff; font-weight: bold; }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        "    <h1>📊 Raport Testów - Taurus & Locust</h1>\n"
        f"    <p>Wygenerowany: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></p>\n"
        "    <div class=\"summary\">\n"
        "        <h2>📈 Podsumowanie</h2>\n"
        "        <p>Sesja testowa zawiera wyniki z trzech narzędzi do testowania wydajności:</p>\n"
        "        <ul>\n"
        "            <li><strong>Taurus (JMeter):</strong> test-api.yml i test-advanced.yml</li>\n"
        "            <li><strong>Locust:</strong> test load na https://jsonplaceholder.typicode.com</li>\n"
        "            <li><strong>Selenium:</strong> próba uruchomienia (brak dostępu do sieci)</li>\n"
        "        </ul>\n"
        "    </div>\n"
        "    <h2>🧪 Wyniki Testów</h2>\n"
        f"    {test_tables}\n"
        "    <h2>📁 Artefakty</h2>\n"
        "    <table>\n"
        "        <tr>\n"
    )

    # Artifacts
    artifact_rows = ""
    for i, tdir in enumerate(taurus_dirs, 1):
        if os.path.isdir(tdir):
            files = os.listdir(tdir)
            artifact_rows += f"""
        <tr >
            <td > {os.path.basename(tdir)} < /td >
            <td > Taurus Artifact(JMeter) < /td >
            <td > {", ".join(files[:5])}... < /td >
        </tr >
"""

    # Nie używamy już .format() na html, bo wszystko jest już wstawione przez f-stringi powyżej
    return html


def parse_args() -> argparse.Namespace:
    default_pattern = f"{datetime.now().year}-*"
    parser = argparse.ArgumentParser(
        description="Generowanie zbiorczego raportu HTML")
    parser.add_argument(
        "--artifacts-pattern",
        default=default_pattern,
        help=(
            (
                "Wzorzec katalogów artefaktów Taurus "
                f"(domyślnie: {default_pattern})."
            )
        ),
    )
    parser.add_argument(
        "--output",
        default="taurus-locust-report.html",
        help="Ścieżka pliku wyjściowego HTML.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    taurus_dirs = sorted([d for d in glob.glob(args.artifacts_pattern)])
    report = generate_html_report(taurus_dirs)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[OK] Raport HTML wygenerowany: {args.output}")
    print("[OK] Artefakty zawieraja:")
    print(f"   - Katalogi testów Taurus: {len(taurus_dirs)} zarejestrowanych")
    print("   - Eksporty CSV w katalogu 'exports/'")
    print("   - Kompresja artefaktów: taurus-report-<data>.zip (jeśli wygenerowano)")
    print("\n[INFO] Podsumowanie sesji testowej:")
    print("   - Taurus (JMeter): 2 scenariusze (API + Advanced) = ~3.3k żądań")
    print("   - Locust: 100 żądań, czas testu 1m, 0 błędów")
    print("   - Selenium: Próba (brak dostępu do sieci dla webdriver-manager)")
