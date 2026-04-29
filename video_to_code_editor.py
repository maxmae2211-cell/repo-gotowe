import subprocess
import os
import re
import requests
from bs4 import BeautifulSoup

# 1. Pobierz film i napisy z YouTube


def download_video_and_subs(url, video_filename=None, subs_lang='en'):
    video_cmd = ["yt-dlp", url]
    if video_filename:
        video_cmd += ["-o", video_filename + ".%(ext)s"]
    subs_cmd = ["yt-dlp", "--write-auto-sub",
                f"--sub-lang={subs_lang}", "--skip-download", url]
    subprocess.run(video_cmd, check=True)
    subprocess.run(subs_cmd, check=True)
    print("Film i napisy pobrane.")

# 2. Jeśli nie ma napisów, transkrybuj audio (Whisper)


def transcribe_audio(audio_path, model='base'):
    import whisper
    model = whisper.load_model(model)
    result = model.transcribe(audio_path)
    with open("transcription.txt", "w", encoding="utf-8") as f:
        f.write(result["text"])
    print("Transkrypcja zapisana do transcription.txt")
    return result["text"]

# 3. Wyciągnij polecenia z napisów/transkrypcji


def extract_commands_from_text(text):
    # Przykład: znajdź polecenia typu "zamień X na Y"
    pattern = r"zamień (.+?) na (.+?)([\.,\n]|$)"
    return re.findall(pattern, text, re.IGNORECASE)

# 4. Nanieś poprawki na plik HTML


def read_and_modify_html(filename, commands):
    with open(filename, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    for old, new, _ in commands:
        html = html.replace(old, new)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Poprawki naniesione w: {filename}")


# Przykład użycia
if __name__ == "__main__":
    yt_url = "https://www.youtube.com/watch?v=ID_FILMU"
    html_file = "vscode-docs.html"
    # 1. Pobierz film i napisy
    download_video_and_subs(yt_url, "moj_film")
    # 2. Pobierz napisy (plik .vtt lub .srt)
    subs_file = None
    for f in os.listdir():
        if f.endswith(".vtt") or f.endswith(".srt"):
            subs_file = f
            break
    if subs_file:
        with open(subs_file, encoding='utf-8') as f:
            text = f.read()
    else:
        # 3. Jeśli nie ma napisów, transkrybuj audio (wymaga ffmpeg i whisper)
        video_file = next((f for f in os.listdir() if f.startswith(
            "moj_film") and f.endswith(".mp4")), None)
        if video_file:
            text = transcribe_audio(video_file)
        else:
            print("Brak pliku wideo do transkrypcji!")
            exit(1)
    # 4. Wyciągnij polecenia
    commands = extract_commands_from_text(text)
    print("Znalezione polecenia:", commands)
    # 5. Nanieś poprawki na HTML
    if commands:
        read_and_modify_html(html_file, commands)
    else:
        print("Brak poleceń do wykonania.")
