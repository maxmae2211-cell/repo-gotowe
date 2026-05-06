import matplotlib.pyplot as plt
import csv
from collections import defaultdict
import os


def plot_response_times(jtl_path, output_dir):
    response_times = defaultdict(list)
    with open(jtl_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row["label"]
            elapsed = int(row["elapsed"])
            response_times[label].append(elapsed)
    for label, times in response_times.items():
        plt.figure(figsize=(10, 5))
        plt.hist(times, bins=30, color='skyblue', edgecolor='black')
        plt.title(f"Histogram czasów odpowiedzi: {label}")
        plt.xlabel("Czas odpowiedzi (ms)")
        plt.ylabel("Liczba próbek")
        plt.grid(True)
        plt.tight_layout()
        out_path = os.path.join(output_dir, f"hist_{label}.png")
        plt.savefig(out_path)
        plt.close()
        print(f"Wygenerowano wykres: {out_path}")

# Przykład użycia:
# plot_response_times('2026-02-12_03-50-11.386922/kpi.jtl', '.')
