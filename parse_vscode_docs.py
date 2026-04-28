import requests
from bs4 import BeautifulSoup

url = "https://code.visualstudio.com/docs"
response = requests.get(url)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

print("Wszystkie linki na stronie:")
for link in soup.find_all("a", href=True):
    print(link["href"], "|", link.text.strip())

print("\nTytuł strony:")
print(soup.title.string)
