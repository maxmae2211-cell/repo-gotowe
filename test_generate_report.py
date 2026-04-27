import unittest
from pathlib import Path
import generate_report

class TestGenerateReport(unittest.TestCase):
    def test_generate_html_report(self):
        # Przygotuj przykładowe katalogi testowe
        test_dir = Path("2026-04-25_23-48-55.387057")
        if not test_dir.exists():
            self.skipTest("Brak przykładowych danych testowych Taurus")
        # Funkcja powinna wygenerować HTML
        html = generate_report.generate_html_report([test_dir])
        self.assertIn("<html", html)
        self.assertIn("Raport Testów", html)

if __name__ == "__main__":
    unittest.main()
