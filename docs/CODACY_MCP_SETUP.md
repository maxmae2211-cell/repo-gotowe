# Konfiguracja Codacy MCP w GitHub Copilot (VS Code)

Przewodnik konfiguracji Codacy MCP (Model Context Protocol) dla GitHub Copilot Chat w Visual Studio Code. MCP działa w stabilnym VS Code oraz w VS Code Insiders.

Źródłem prawdy jest plik **`.vscode/mcp.json`** w tym repozytorium — definiuje serwer `codacy`, który VS Code uruchamia lokalnie. Na github.com nie ma przycisku „Add MCP Server” dla serwerów VS Code; nie konfiguruj Codacy przez ustawienia GitHub.

## 📋 Spis treści

- [Wymagania](#-wymagania)
- [Konfiguracja w repozytorium](#-konfiguracja-w-repozytorium)
- [Uruchomienie serwera](#-uruchomienie-serwera)
- [Ustawienia GitHub / organizacji](#-ustawienia-github--organizacji)
- [Troubleshooting](#-troubleshooting)
- [Weryfikacja konfiguracji](#️-weryfikacja-konfiguracji)

---

## ✅ Wymagania

- Visual Studio Code (stabilny lub Insiders) w aktualnej wersji
- Rozszerzenie GitHub Copilot / Copilot Chat
- Node.js — `node` i `npx` muszą być dostępne w PATH procesu VS Code (`node --version`, `npx --version`)
- Konto Codacy z dostępem do projektu i Account API Token

---

## 🔧 Konfiguracja w repozytorium

Plik `.vscode/mcp.json`:

```jsonc
{
  "inputs": [
    {
      "id": "codacy_token",
      "type": "promptString",
      "description": "Codacy Account Token (https://app.codacy.com/account/access-management)",
      "password": true
    }
  ],
  "servers": {
    "codacy": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@codacy/codacy-mcp@latest"],
      "env": {
        "CODACY_ACCOUNT_TOKEN": "${input:codacy_token}"
      }
    }
  }
}
```

- `command: "npx"` działa na Windows, macOS i Linux (nie używaj `npx.cmd`).
- Token **nie** jest zapisywany w repo — VS Code pyta o niego przy pierwszym starcie serwera (`${input:codacy_token}`) i przechowuje go bezpiecznie. Nigdy nie wpisuj tokena bezpośrednio do `mcp.json`.

### Token Codacy

1. Otwórz https://app.codacy.com/account/access-management
2. Utwórz **Account API Token** i skopiuj go
3. Wklej go, gdy VS Code poprosi o `codacy_token`

---

## ▶️ Uruchomienie serwera

1. Otwórz folder repozytorium w VS Code (zaufaj workspace)
2. Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) → `MCP: List Servers` → `codacy` → **Start Server**
   - alternatywnie: akcja CodeLens **Start** nad serwerem w `.vscode/mcp.json`
3. Potwierdź zaufanie do serwera i podaj token, gdy VS Code o to poprosi
4. Otwórz Copilot Chat w trybie **Agent** i sprawdź w selektorze narzędzi (**Configure Tools**), że narzędzia Codacy są widoczne

---

## 🏢 Ustawienia GitHub / organizacji

Serwer jest definiowany w repo, ale Copilot musi mieć zgodę na użycie MCP:

- Ustawienie VS Code `chat.mcp.enabled` musi być włączone
- Konto osobiste: https://github.com/settings/copilot/features — opcja *MCP servers in Copilot* musi być włączona
- Organizacja (Copilot Business/Enterprise): https://github.com/organizations/{organization-name}/settings/copilot/features — polityka MCP ustawiana przez Owner/Admin. Jeśli jest wyłączona, poproś administratora o jej włączenie.

---

## 🐛 Troubleshooting

| Objaw | Działanie |
|-------|-----------|
| Serwer nie startuje / `npx` not found | Sprawdź `node --version` i `npx --version`; dodaj Node.js do PATH i zrestartuj VS Code |
| Brak szczegółów błędu | `MCP: List Servers` → `codacy` → **Show Output** |
| Serwer wisi lub po zmianie `mcp.json` | `MCP: List Servers` → `codacy` → **Restart Server** |
| `401 Unauthorized` | Token zły lub wygasły — wygeneruj nowy na https://app.codacy.com/account/access-management, zaktualizuj wartość inputu `codacy_token` (CodeLens w `.vscode/mcp.json`) i zrestartuj serwer |
| Narzędzia Codacy nie widoczne w Chat | `MCP: Reset Cached Tools`, potem restart serwera |
| Odrzucono zaufanie / serwer zablokowany | `MCP: Reset Trust`, potem **Start Server** i ponowne potwierdzenie |
| Nadal nie działa | `Developer: Reload Window` |
| MCP wyłączone w organizacji | Poproś admina o włączenie *MCP servers in Copilot* |

Brak analizy w Codacy? Upewnij się, że repozytorium jest dodane na https://app.codacy.com.

---

## ✔️ Weryfikacja konfiguracji

1. `MCP: List Servers` — `codacy` ma status **Running**
2. **Show Output** dla `codacy` — brak błędów startu i `401`
3. Copilot Chat (Agent) → **Configure Tools** — narzędzia Codacy (np. `codacy_cli_analyze`) są dostępne
4. Poproś w Chat: „Przeanalizuj plik X przez Codacy” — agent powinien wywołać narzędzie Codacy

---

## 📚 Przydatne linki

- 🔗 [VS Code — MCP servers](https://code.visualstudio.com/docs/agent-customization/mcp-servers)
- 🔗 [Codacy MCP Server](https://github.com/codacy/codacy-mcp-server)
- 🔗 [Codacy Access Management (tokeny)](https://app.codacy.com/account/access-management)
- 🔗 [Codacy Documentation](https://docs.codacy.com)
- 🔗 [GitHub Copilot Features](https://github.com/settings/copilot/features)

---

## ❓ FAQ

**P: Czy Codacy MCP działa w zwykłym VS Code?**
O: Tak. MCP jest dostępne w stabilnym VS Code oraz w VS Code Insiders.

**P: Czy mogę używać Codacy MCP bez organizacji?**
O: Tak — wystarczy konto osobiste z włączonym *MCP servers in Copilot*.

**P: Jak przestać używać Codacy MCP?**
O: `MCP: List Servers` → `codacy` → **Stop Server** (lub **Disable**).

---

## 📞 Wsparcie

1. Przejdź przez sekcję [Troubleshooting](#-troubleshooting) oraz `CI-CD-RUNBOOK.md`
2. Otwórz issue: [repo-gotowe/issues](https://github.com/maxmae2211-cell/repo-gotowe/issues)
3. Support Codacy: https://support.codacy.com

---

**Ostatnia aktualizacja:** 2026-10-02
**Status:** ✅ Aktualna dokumentacja
