import requests

import subprocess

# Pobieranie strony internetowej (HTML)
def download_page(url, filename):
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, 'w', encoding=response.encoding or 'utf-8') as f:
        f.write(response.text)
    print(f"Strona zapisana do: {filename}")

# Pobieranie pliku (np. wideo, obraz, pdf)
def download_file(url, filename):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"Plik pobrany do: {filename}")

if __name__ == "__main__":
    # Przykład użycia
    # Pobierz stronę
    download_page('https://www.example.com', 'example.html')
    # Pobierz plik wideo (mp4)
    # download_file('https://www.example.com/video.mp4', 'video.mp4')

    # Pobierz film z YouTube (lub innego serwisu obsługiwanego przez yt-dlp)
    # download_video('https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'moj_film')


def download_video(url, filename=None):
    """
    Pobiera film z YouTube lub innego serwisu obsługiwanego przez yt-dlp.
    Wymaga zainstalowanego pakietu yt-dlp.
    :param url: URL filmu
    :param filename: (opcjonalnie) ścieżka docelowa pliku (bez rozszerzenia)
    """
    command = ["yt-dlp", url]
    if filename:
        command += ["-o", filename + ".%(ext)s"]
    try:
        subprocess.run(command, check=True)
    except Exception as e:
        print(f"Błąd pobierania filmu: {e}")
