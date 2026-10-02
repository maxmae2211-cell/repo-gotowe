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

### Krok 1: Włącz MCP servers w Copilot (konto GitHub)

1. Przejdź do: https://github.com/settings/copilot/features
2. Upewnij się, że opcja **MCP servers in Copilot** jest **włączona**

### Krok 2: Włącz MCP w VS Code

1. Ustawienie `chat.mcp.enabled` musi mieć wartość `true` (Settings → wyszukaj `mcp`)
2. Zaktualizuj rozszerzenia **GitHub Copilot** i **GitHub Copilot Chat**
3. Upewnij się, że `node` i `npx` działają w terminalu (`npx --version`)

### Krok 3: Konfiguracja serwera w repozytorium

Repozytorium zawiera gotową konfigurację w `.vscode/mcp.json`:

```jsonc
{
  "inputs": [
    { "id": "codacy_token", "type": "promptString", "description": "Codacy Account Token", "password": true }
  ],
  "servers": {
    "codacy": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@codacy/codacy-mcp@latest"],
      "env": { "CODACY_ACCOUNT_TOKEN": "${input:codacy_token}" }
    }
  }
}
```

- Przy pierwszym starcie serwera VS Code poprosi o **Codacy Account Token**
  (https://app.codacy.com/account/access-management) i zapisze go w Secret Storage.
- **Nigdy** nie wpisuj tokena bezpośrednio do `.vscode/mcp.json` ani innych plików w repo.

---

## 🏢 Konfiguracja na poziomie organizacji

### Krok 1: Dostęp do ustawień organizacji

1. Przejdź do: https://github.com/organizations/{organization-name}/settings/copilot/features
   - Zamień `{organization-name}` na nazwę Twojej organizacji
2. Musisz mieć uprawnienia **Owner** lub **Admin** organizacji

### Krok 2: Włącz politykę MCP dla organizacji

1. W sekcji polityk Copilot ustaw **MCP servers in Copilot** na **Enabled**
   (dla Copilot Business/Enterprise jest domyślnie wyłączona)
2. Zapisz — członkowie organizacji mogą wtedy uruchamiać serwery MCP skonfigurowane w `.vscode/mcp.json`

---

## 🐛 Troubleshooting - VS Code Insiders

### Problem 1: Codacy MCP się nie łączy

**Przyczyny i rozwiązania:**

1. **MCP servers nie są włączone**
   - https://github.com/settings/copilot/features → **MCP servers in Copilot** = ON
   - VS Code: `chat.mcp.enabled` = `true`
   - Reset w rozszerzeniu: `MCP: List Servers` → `codacy` → **Restart Server**, potem `MCP: Reset Cached Tools`

2. **Brakuje API tokena**
   - Wygeneruj nowy token na: https://app.codacy.com/account/access-management
   - Podaj go, gdy VS Code poprosi o input `codacy_token` (start serwera z `.vscode/mcp.json`)

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

2. Zrestartuj serwer Codacy MCP:
   - `MCP: List Servers` → `codacy` → **Restart Server**
   - `MCP: Reset Cached Tools` (i `MCP: Reset Trust`, jeśli serwer był odrzucony)
   - `Developer: Reload Window`
   - Sprawdź log: `MCP: List Servers` → `codacy` → **Show Output**

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

1. Wygeneruj nowy token na https://app.codacy.com/account/access-management
2. Zrestartuj serwer `codacy` (`MCP: List Servers` → **Restart Server**) i podaj nowy token dla inputu `codacy_token`
3. Sprawdź log: **Show Output** — nie powinno być błędu 401

---

## ✔️ Weryfikacja konfiguracji

### Jak sprawdzić, czy Codacy MCP działa?

1. **W VS Code Insiders:**
   - Otwórz paleta komend: `Cmd+Shift+P` (macOS) lub `Ctrl+Shift+P` (Windows/Linux)
   - Wpisz: `MCP: List Servers`
   - Powinieneś zobaczyć **`codacy`** ze statusem *Running*

2. **Testuj integrację:**
   - Otwórz Copilot Chat w trybie **Agent**
   - W selektorze narzędzi powinny być widoczne narzędzia `codacy_*` (np. `codacy_cli_analyze`)
   - Poproś: „Uruchom analizę Codacy dla zmienionego pliku”

3. **Sprawdź logi:**
   - Otwórz Output panel: `Cmd+Shift+U` (macOS) lub `Ctrl+Shift+U` (Windows/Linux)
   - Albo: `MCP: List Servers` → `codacy` → **Show Output**

---

## 📚 Przydatne linki

- 🔗 [MCP servers in VS Code](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
- 🔗 [Codacy MCP Server](https://github.com/codacy/codacy-mcp-server)
- 🔗 [Codacy Documentation](https://docs.codacy.com)
- 🔗 [Codacy Account Tokens](https://app.codacy.com/account/access-management)
- 🔗 [GitHub Copilot Settings](https://github.com/settings/copilot)
- 🔗 [VS Code Insiders Download](https://code.visualstudio.com/insiders/)

---

## ❓ FAQ

**P: Czy Codacy MCP działa w zwykłym VS Code?**
O: Tak. MCP jest obsługiwane w stabilnym VS Code (z GitHub Copilot Chat) — konfiguracja z `.vscode/mcp.json` działa tak samo jak w Insiders.

**P: Czy mogę używać Codacy MCP bez konta organizacji?**
O: Tak! Możesz skonfigurować na poziomie osobistym (Personal Account).

**P: Jak wylogować się z Codacy MCP?**
O: `MCP: List Servers` → `codacy` → **Stop Server** (lub usuń wpis `codacy` z lokalnej kopii `.vscode/mcp.json`).

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
