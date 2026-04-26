import requests
from bs4 import BeautifulSoup
import re
from download_utils import download_video

def get_latest_youtube_videos(channel_url, max_videos=3):
    """
    Pobiera listę URL najnowszych filmów z kanału YouTube.
    """
    response = requests.get(channel_url + "/videos")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    video_urls = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.match(r"^/watch\?v=", href):
            video_urls.add("https://www.youtube.com" + href)
        if len(video_urls) >= max_videos:
            break
    return list(video_urls)

if __name__ == "__main__":
    channel = "https://www.youtube.com/@code"
    print("Pobieram najnowsze filmy z kanału:", channel)
    urls = get_latest_youtube_videos(channel, max_videos=3)
    for url in urls:
        print("Pobieram film:", url)
        download_video(url)
    print("Gotowe! Otwórz pobrane pliki .mp4 w VS Code przez Video Preview.")
