# Rejestr Pracowników AI

Wszyscy agenci AI repozytorium `repo-gotowe`. Foldery zadań i raportów są lokalne (w `pracownicy/`), pliki wspólne (neochat.py, config.json, RUNBOOK-TAURUS.md) zostają w root repo.

| Plik | Rola | Plik zadań | Plik raportu | Opis |
|------|------|-----------|--------------|------|
| pracownik.py | Pracownik (Ogólny Agent) | zadania.txt | raport-pracownik.txt | Autonomiczny agent ogólnego przeznaczenia — wykonuje dowolne zadania AI na podstawie listy w pliku zadań |
| pracownik2.py | Pracownik2 (Ekspert Taurus) | — | raport-pracownik2.txt | Analiza wyników testów Taurus/JMeter, generowanie wpisów do RUNBOOK-TAURUS.md, sugestie PR (qq→main) |
| pracownik3.py | Pracownik3 (Taurus Pipeline) | — | — | Taurus pipeline z fallback — działa bez klucza AI, szuka JTL w root repo i aktualizuje RUNBOOK |
| pracownik4.py | Pracownik4 (Finder AI) | — | pracownik4.log | Diagnozuje dostępnych providerów AI: OpenAI/GitHub Models, Groq, Ollama, LMStudio, Pollinations |
| pracownik5.py | Pracownik5 (Spec. Aktualizacji) | zadania-aktualizacja.txt | raport-aktualizacja.txt | Audyt kodu, aktualizacje bibliotek, planowanie sprintów, modernizacja projektu |

## Importy i ścieżki

- Każdy pracownik definiuje:
  - `BASE_DIR = Path(__file__).parent` → katalog `pracownicy/` (lokalne pliki zadań/raportów)
  - `ROOT_DIR = Path(__file__).resolve().parent.parent` → root repozytorium (neochat.py, config.json, RUNBOOK-TAURUS.md, katalogi Taurus)
- `sys.path.insert(0, str(ROOT_DIR))` — umożliwia importy `neochat`, `ai_backend`, `moderacja` z root repo
- pracownik3.py dodatkowo: `sys.path.insert(0, str(Path.home() / "Desktop" / "moj-ai"))` (fallback Desktop AI)

## Wspólne zależności (w root repo)

- `neochat.py` — warstwa AI (load_config, wyslij_do_ai)
- `ai_backend.py` — multi-provider backend (wyslij_do_ai_multi)
- `moderacja.py` — moderacja wejścia/wyjścia
- `config.json` — konfiguracja API keys
- `RUNBOOK-TAURUS.md` — runbook pipeline Taurus (edytowany przez pracownik2/3)
