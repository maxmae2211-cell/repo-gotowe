import requests
from bs4 import BeautifulSoup
import subprocess
import os


def download_page(url, filename):
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, 'w', encoding=response.encoding or 'utf-8') as f:
        f.write(response.text)
    print(f"Strona zapisana do: {filename}")


def read_and_modify_html(filename, instructions):
    with open(filename, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    # Zamiana tekstu według instrukcji
    for old, new in instructions.get("replace", []):
        html = html.replace(old, new)
    # Usuwanie elementów po selektorze
    for selector in instructions.get("remove", []):
        for tag in soup.select(selector):
            tag.decompose()
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f"Poprawki naniesione w: {filename}")


def download_video(url, filename=None):
    command = ["yt-dlp", url]
    if filename:
        command += ["-o", filename + ".%(ext)s"]
    subprocess.run(command, check=True)
    print(f"Film pobrany: {filename or url}")


# Przykład użycia
if __name__ == "__main__":
    # Pobierz stronę
    download_page("https://code.visualstudio.com/docs", "vscode-docs.html")
    # Nanieś poprawki na HTML
    read_and_modify_html("vscode-docs.html", {
        "replace": [("Visual Studio", "VS")],
        "remove": ["footer"]
    })
    # Pobierz film z YouTube
    download_video("https://www.youtube.com/watch?v=ID_FILMU", "moj_film")
