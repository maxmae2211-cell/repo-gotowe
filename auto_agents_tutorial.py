import requests
from bs4 import BeautifulSoup
import os

url = "https://code.visualstudio.com/docs/copilot/agents/agents-tutorial"
response = requests.get(url)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

# 1. Podsumowanie tutoriala
with open("AGENT_TUTORIAL_SUMMARY.md", "w", encoding="utf-8") as f:
    f.write(f"# {soup.title.string}\n\n")
    for h in soup.find_all(["h1", "h2", "h3"]):
        f.write(f"## {h.text.strip()}\n")
    f.write("\n---\nPierwsze 10 akapitów:\n\n")
    for p in soup.find_all("p")[:10]:
        f.write(f"- {p.text.strip()}\n")

# 2. Szablon agenta (prosty Python)
with open("agent_template.py", "w", encoding="utf-8") as f:
    f.write("""class Agent:
    def __init__(self, name):
        self.name = name
    def run(self):
        print(f'Agent {self.name} działa!')

if __name__ == '__main__':
    agent = Agent('DemoAgent')
    agent.run()
""")

# 3. Pobierz i zapisz wszystkie linki (tylko pliki, obrazy, PDF)
resource_links = []
for link in soup.find_all("a", href=True):
    href = link["href"]
    if any(href.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"]):
        resource_links.append(href)
        try:
            r = requests.get(href if href.startswith("http")
                             else f"https://code.visualstudio.com{href}")
            filename = os.path.basename(href)
            with open(filename, "wb") as out:
                out.write(r.content)
        except Exception as e:
            print(f"Błąd pobierania {href}: {e}")

with open("AGENT_LINKED_RESOURCES.txt", "w", encoding="utf-8") as f:
    for l in resource_links:
        f.write(l + "\n")

# 4. Aktualizacja README.md
readme_path = "README.md"
summary_header = "## Agent Tutorial Summary"
summary_content = open("AGENT_TUTORIAL_SUMMARY.md", encoding="utf-8").read()
summary = f"\n\n{summary_header}\n" + summary_content
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()
    if summary_header not in readme:
        with open(readme_path, "a", encoding="utf-8") as f:
            f.write(summary)
    else:
        print(
            f"Sekcja '{summary_header}' już istnieje w README.md - pomijam duplikat.")
else:
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(summary)

print("Automatyzacja zakończona. Wygenerowano: AGENT_TUTORIAL_SUMMARY.md, agent_template.py, AGENT_LINKED_RESOURCES.txt, zaktualizowano README.md.")
