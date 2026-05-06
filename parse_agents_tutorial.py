import requests
from bs4 import BeautifulSoup

url = "https://code.visualstudio.com/docs/copilot/agents/agents-tutorial"
response = requests.get(url)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

print("Tytuł strony:")
print(soup.title.string)

print("\nWszystkie nagłówki (h1-h3):")
for h in soup.find_all(["h1", "h2", "h3"]):
    print(h.name, "|", h.text.strip())

print("\nWszystkie linki na stronie:")
for link in soup.find_all("a", href=True):
    print(link["href"], "|", link.text.strip())

print("\nPierwsze 10 akapitów:")
for p in soup.find_all("p")[:10]:
    print(p.text.strip())
