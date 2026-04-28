import requests
from bs4 import BeautifulSoup
import os

# Lista sekcji i URL (przykładowe, rozbuduj według potrzeb)
SECTIONS = [
    ("Przegląd", "https://code.visualstudio.com/docs"),
    ("Przygotowanie", "https://code.visualstudio.com/docs/setup/setup-overview"),
    ("Zacznij", "https://code.visualstudio.com/docs/getstarted/getting-started"),
    ("GitHub Copilot", "https://code.visualstudio.com/docs/copilot/overview"),
    ("Agent Tutorial", "https://code.visualstudio.com/docs/copilot/agents/agents-tutorial"),
    ("Planowanie", "https://code.visualstudio.com/docs/copilot/agents/planning"),
    ("Pamięć", "https://code.visualstudio.com/docs/copilot/agents/memory"),
    ("Narzędzia", "https://code.visualstudio.com/docs/copilot/agents/tools"),
    ("Czat", "https://code.visualstudio.com/docs/copilot/chat/overview"),
    ("Personalizacja", "https://code.visualstudio.com/docs/copilot/guides/customize-copilot-guide"),
    ("Sugestie inline", "https://code.visualstudio.com/docs/editor/intellisense"),
    ("Debugowanie", "https://code.visualstudio.com/docs/editor/debugging"),
    ("Kontrola wersji", "https://code.visualstudio.com/docs/sourcecontrol/overview"),
    ("Terminal", "https://code.visualstudio.com/docs/terminal/basics"),
    ("Python", "https://code.visualstudio.com/docs/python/python-tutorial"),
    ("Node.js", "https://code.visualstudio.com/docs/nodejs/working-with-javascript"),
    ("Data Science", "https://code.visualstudio.com/docs/datascience/overview"),
    # Dodaj kolejne sekcje według potrzeb...
]

def fetch_and_summarize(url, out_dir, images_dir, section_links, section_name=None):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string if soup.title else url
    filename = os.path.join(out_dir, f"{title[:40].replace(' ', '_').replace('/', '_')}.md")
    anchor = section_name.lower().replace(" ", "-") if section_name else None
    with open(filename, "w", encoding="utf-8") as f:
        # Nagłówek z linkiem do oryginału i kotwicą do spisu treści
        if section_name:
            f.write(f'<a name="{anchor}"></a>\n')
            f.write(f"# [{section_name}]({url})\n\n")
        else:
            f.write(f"# {title}\n\n")
        # Linkowanie nagłówków
        for h in soup.find_all(["h1", "h2", "h3"]):
            h_text = h.text.strip()
            for sec_name, sec_url in section_links.items():
                if sec_name in h_text:
                    h_text = h_text.replace(sec_name, f"[{sec_name}]({sec_url})")
            f.write(f"## {h_text}\n")
        f.write("\n---\nPierwsze 5 akapitów:\n\n")
        for p in soup.find_all("p")[:5]:
            text = p.text.strip()
            # Automatyczne linkowanie nazw sekcji
            for sec_name, sec_url in section_links.items():
                if sec_name in text:
                    text = text.replace(sec_name, f"[{sec_name}]({sec_url})")
            f.write(f"- {text}\n")
        # Pobierz obrazy
        imgs = soup.find_all("img")
        if imgs:
            f.write("\n---\nObrazy:\n")
            for img in imgs:
                src = img.get("src")
                if src and not src.startswith("data:"):
                    img_url = src if src.startswith("http") else requests.compat.urljoin(url, src)
                    img_name = os.path.basename(img_url.split("?")[0])
                    try:
                        r = requests.get(img_url)
                        with open(os.path.join(images_dir, img_name), "wb") as out:
                            out.write(r.content)
                        f.write(f"- ![]({os.path.join('images', img_name)})\n")
                    except Exception as e:
                        f.write(f"- [Błąd pobierania obrazu: {img_url}]\n")
    print(f"Podsumowanie zapisane: {filename}")

if __name__ == "__main__":
    out_dir = "docs_summary"
    images_dir = os.path.join(out_dir, "images")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    # Słownik do linkowania nazw sekcji
    section_links = {name: url for name, url in SECTIONS}
    all_docs = []
    toc = ["# Spis treści\n"]
    for name, url in SECTIONS:
        anchor = name.lower().replace(" ", "-")
        toc.append(f"- [{name}](#{anchor}) ([oryginał]({url}))")
    for name, url in SECTIONS:
        print(f"Pobieram i analizuję: {name} -> {url}")
        try:
            fetch_and_summarize(url, out_dir, images_dir, section_links, section_name=name)
            # Dodaj do zbiorczego markdown
            md_files = [f for f in os.listdir(out_dir) if f.endswith('.md')]
            if md_files:
                with open(os.path.join(out_dir, md_files[-1]), encoding="utf-8") as f:
                    all_docs.append(f.read())
        except Exception as e:
            print(f"Błąd dla {url}: {e}")
    # Zbiorczy plik ze spisem treści
    with open(os.path.join(out_dir, "ALL_DOCS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(toc) + "\n\n---\n\n" + "\n\n---\n\n".join(all_docs))
    print("\nSzkielet pobierania, podsumowania, pobierania obrazów, linkowania i spisu treści gotowy!")
