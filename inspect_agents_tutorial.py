import requests
from bs4 import BeautifulSoup

url = "https://code.visualstudio.com/docs/copilot/agents/agents-tutorial"
response = requests.get(url)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

print("--- INSPEKCJA STRONY ---\n")
print(f"Tytuł: {soup.title.string}\n")

print("Nagłówki (h1-h3):")
for h in soup.find_all(["h1", "h2", "h3"]):
    print(f"  {h.name}: {h.text.strip()}")

print("\nLiczba akapitów:", len(soup.find_all("p")))
print("Pierwsze 3 akapity:")
for p in soup.find_all("p")[:3]:
    print(f"  - {p.text.strip()}")

print("\nLiczba linków:", len(soup.find_all("a", href=True)))
print("Przykładowe linki:")
for link in soup.find_all("a", href=True)[:5]:
    print(f"  - {link['href']} | {link.text.strip()}")

print("\nLiczba obrazów:", len(soup.find_all("img")))
if soup.find_all("img"):
    print("Przykładowe obrazy:")
    for img in soup.find_all("img")[:3]:
        print(f"  - {img.get('src')}")

print("\nStruktura sekcji:")
for section in soup.find_all(['section', 'article', 'nav']):
    print(f"  {section.name} | class: {section.get('class')}")

print("\n--- KONIEC INSPEKCJI ---")
