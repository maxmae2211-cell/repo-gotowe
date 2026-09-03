# Konfiguracja Codacy MCP w GitHub Copilot

Przewodnik pełny do setupu Codacy MCP (Model Context Protocol) dla konta osobistego i organizacji w Visual Studio Code Insiders.

## 📋 Spis treści

- [Wymagania](#wymagania)
- [Konfiguracja na poziomie osobistym](#konfiguracja-na-poziomie-osobistym)
- [Konfiguracja na poziomie organizacji](#konfiguracja-na-poziomie-organizacji)
- [Troubleshooting - VS Code Insiders](#troubleshooting---vs-code-insiders)
- [Weryfikacja konfiguracji](#weryfikacja-konfiguracji)

---

## ✅ Wymagania

- Visual Studio Code Insiders (najnowsza wersja)
- GitHub Copilot extension zainstalowany i aktualny
- Konto GitHub
- Codacy API token (dostępny w ustawieniach Codacy)
- Dostęp do projektu na Codacy

---

## 🔧 Konfiguracja na poziomie osobistym

### Krok 1: Włącz MCP servers w Copilot

1. Otwórz VS Code Insiders
2. Przejdź do: **Settings > Copilot > Enable MCP servers in Copilot**
3. Upewnij się, że opcja jest **włączona** (toggle powinien być zielony)

### Krok 2: Konfiguracja w ustawieniach GitHub

1. Przejdź do: https://github.com/settings/copilot/features
2. Szukaj sekcji **"MCP Servers"** lub **"Codacy"**
3. Kliknij **"Add MCP Server"** lub **"Configure"**
4. Wprowadź następujące dane:
   - **Nazwa**: `Codacy`
   - **Typ**: `MCP Server`
   - **URL/Endpoint**: Zgodnie z dokumentacją Codacy MCP
   - **API Token**: Twój token z konta Codacy

### Krok 3: Zapisz ustawienia

- Kliknij **Save** lub **Apply**
- Restart VS Code Insiders (jeśli jest wymagany)

---

## 🏢 Konfiguracja na poziomie organizacji

### Krok 1: Dostęp do ustawień organizacji

1. Przejdź do: https://github.com/organizations/{organization-name}/settings/copilot/features
   - Zamień `{organization-name}` na nazwę Twojej organizacji
2. Musisz mieć uprawnienia **Owner** lub **Admin** organizacji

### Krok 2: Dodaj Codacy MCP dla organizacji

1. W sekcji **"MCP Servers"** kliknij **"Add Organization MCP Server"**
2. Wprowadź:
   - **Nazwa**: `Codacy`
   - **Opis**: `Codacy code quality analysis`
   - **Konfiguracja**: Domyślna lub niestandardowa (zależnie od potrzeb)
3. Ustaw **uprawnienia dostępu** (którzy członkowie organizacji mogą używać)

### Krok 3: Zastosuj dla wszystkich repozytoriów (opcjonalnie)

- Zaznacz opcję **"Apply to all repositories"** jeśli chcesz, aby Codacy MCP był dostępny dla wszystkich projektów w organizacji
- Lub wybierz konkretne repozytoria

### Krok 4: Zapisz

- Kliknij **Save** lub **Update Settings**

---

## 🐛 Troubleshooting - VS Code Insiders

### Problem 1: Codacy MCP się nie łączy

**Przyczyny i rozwiązania:**

1. **MCP servers nie są włączone**
   ```
   Settings > Copilot > Enable MCP servers in Copilot
   ```
   - Upewnij się, że jest **ON**

2. **Brakuje API tokena**
   - Wygeneruj nowy token na: https://app.codacy.com/account/api-tokens
   - Dodaj go w: `GitHub Settings > Copilot > Features > MCP Servers > Codacy`

3. **VS Code Insiders nie ma najnowszej wersji**
   ```bash
   # Sprawdź wersję
   code-insiders --version
   
   # Zaktualizuj (auto, ale możesz też ręcznie)
   # Jeśli macOS: Odinstaluj i pobierz najnowszą wersję
   # Jeśli Windows/Linux: Update powinien być automatyczny
   ```

4. **Copilot extension jest przestarzały**
   - Przejdź do: Extensions in VS Code
   - Szukaj: `GitHub Copilot`
   - Kliknij **Update** jeśli jest dostępny
   - Restart VS Code Insiders

### Problem 2: "MCP Server not found" lub "Connection failed"

**Rozwiązanie:**

1. Sprawdź czy Codacy API endpoint jest dostępny:
   ```bash
   curl -H "Authorization: token YOUR_CODACY_TOKEN" https://api.codacy.com/api/v3/status
   ```

2. Usuń i dodaj Codacy MCP od nowa:
   - GitHub Settings > Copilot > Features
   - Usuń Codacy MCP
   - Restart VS Code
   - Dodaj ponownie

3. Sprawdź firewall/proxy:
   - Może być blokowana komunikacja z Codacy API
   - Skontaktuj się z administratorem IT

### Problem 3: Copilot nie sugeruje Codacy analizy

**Przyczyny:**

- Codacy MCP nie jest jeszcze w pełni zintegrowany w Twoim projekcie
- Brakuje konfiguracji `.codacy.yml` w repozytorium
- Codacy nie skanuje jeszcze Twojego projektu

**Rozwiązanie:**

1. Upewnij się, że projekt jest dodany w Codacy: https://app.codacy.com
2. Dodaj `.codacy.yml` w root repozytorium:
   ```yaml
   ---
   exclude_paths:
     - docs
     - node_modules
   ```
3. Poczekaj na skan (zwykle 5-10 minut)
4. Restart VS Code Insiders

### Problem 4: Authorization error / 401 Unauthorized

**Przyczyna:** Token API jest nieprawidłowy lub wygasł

**Rozwiązanie:**

1. Wygeneruj nowy token na https://app.codacy.com/account/api-tokens
2. Skopiuj token
3. Przejdź do GitHub Settings > Copilot > Features > Codacy MCP
4. Zaktualizuj token
5. Kliknij **Test Connection** (jeśli dostępne)
6. Zapisz i restart VS Code

---

## ✔️ Weryfikacja konfiguracji

### Jak sprawdzić, czy Codacy MCP działa?

1. **W VS Code Insiders:**
   - Otwórz paleta komend: `Cmd+Shift+P` (macOS) lub `Ctrl+Shift+P` (Windows/Linux)
   - Wpisz: `Copilot: Show MCP Servers`
   - Powinieneś zobaczyć **"Codacy"** na liście aktywnych serwerów

2. **Testuj integrację:**
   - Otwórz plik z kodem
   - Napisz komentarz: `// @codacy analyze`
   - Copilot powinien zasugerować analizę z Codacy

3. **Sprawdź logi:**
   - Otwórz Output panel: `Cmd+Shift+U` (macOS) lub `Ctrl+Shift+U` (Windows/Linux)
   - Szukaj loga Copilot
   - Powinieneś zobaczyć wpisy dotyczące Codacy MCP

---

## 📚 Przydatne linki

- 🔗 [GitHub Copilot MCP Documentation](https://github.com/github-copilot/mcp-protocol)
- 🔗 [Codacy Documentation](https://docs.codacy.com)
- 🔗 [Codacy API Tokens](https://app.codacy.com/account/api-tokens)
- 🔗 [GitHub Copilot Settings](https://github.com/settings/copilot)
- 🔗 [VS Code Insiders Download](https://code.visualstudio.com/insiders/)

---

## ❓ FAQ

**P: Czy Codacy MCP działa w zwykłym VS Code?**
O: Na razie MCP jest testowo dostępne głównie w VS Code Insiders. Zwykły VS Code ma ograniczoną obsługę.

**P: Czy mogę używać Codacy MCP bez konta organizacji?**
O: Tak! Możesz skonfigurować na poziomie osobistym (Personal Account).

**P: Jak wylogować się z Codacy MCP?**
O: GitHub Settings > Copilot > Features > Codacy MCP > Remove/Disconnect

**P: Czy Codacy MCP jest darmowy?**
O: Dostęp do MCP zależy od Twojego planu Codacy i GitHub Copilot.

---

## 📞 Wsparcie

Jeśli problemy się utrzymują:

1. Sprawdź najnowszą wersję VS Code Insiders
2. Zaktualizuj GitHub Copilot extension
3. Otwórz issue na GitHub: [repo-gotowe/issues](https://github.com/maxmae2211-cell/repo-gotowe/issues)
4. Skontaktuj się z supportem Codacy: https://support.codacy.com

---

**Ostatnia aktualizacja:** 2026-09-03  
**Status:** ✅ Aktualna dokumentacja
