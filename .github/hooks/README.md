# Git Hooks — guard-git

Katalog zawiera szablony hooków Git oraz skrypt ochrony przed niebezpiecznymi komendami.

## Pliki

| Plik | Opis |
|---|---|
| `guard-git.json` | Konfiguracja — lista blokowanych komend i wzorców plików |
| `scripts/guard-git.ps1` | PowerShell hook (pre-commit) — blokuje staged wrażliwe pliki |
| `post-commit` | Hook post-commit (sh, cross-platform) — podsumowanie commitu i ostrzeżenie o wrażliwych plikach |
| `install-hooks.ps1` | Instalator hooków (wszystkie platformy — wymaga `pwsh`) |

## Instalacja

Jeden skrypt `install-hooks.ps1` działa na wszystkich platformach — wymaga [PowerShell Core (pwsh)](https://github.com/PowerShell/PowerShell).

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File .github\hooks\install-hooks.ps1
```

### Linux / macOS (pwsh)

```bash
pwsh .github/hooks/install-hooks.ps1
```

## Działanie po instalacji

- **pre-commit** — uruchamia `guard-git.ps1 -HookType pre-commit`, blokuje commit jeśli w stage są wrażliwe pliki (`.env`, `.bzt-rc`, klucze prywatne itp.); ostrzega przy commitowaniu prosto do `main`/`master`
- **pre-push** — uruchamia `guard-git.ps1 -HookType pre-push`, blokuje force-push do chronionych gałęzi
- **post-commit** — wyświetla podsumowanie: gałąź, skrót SHA, wiadomość commitu, liczba plików; ostrzega o potencjalnie wrażliwych plikach

## Konfiguracja `guard-git.json`

```json
{
  "blocked_file_patterns": ["*.env", ".bzt-rc", "*.key", ...],
  "protected_branches": ["main", "master"],
  "warn_only": false
}
```

Ustaw `"warn_only": true` aby hook tylko ostrzegał zamiast blokować.
