# Copilot Instructions — repo-gotowe

## Projekt

Load testing z Taurus/bzt, integracja z BlazeMeter. Windows, Python 3.10.

## Kluczowe zasady

- Używaj PowerShell (nie cmd/bash) dla komend Windows
- Token BlazeMeter jest w `~/.bzt-rc` — NIGDY nie dodawaj tokenów do plików w repo
- Testy uruchamiaj przez `scripts/run-taurus.ps1`, nie bezpośrednio przez `bzt`
- Po zmianach w plikach `.yml` zawsze waliduj składnię YAML
- Commit i push po każdej zakończonej zmianie

## AutoAgent

Workspace zawiera autonomicznego agenta w `.github/agents/auto-agent.agent.md`.
Agent może samodzielnie: edytować pliki, uruchamiać komendy, obsługiwać przeglądarkę, robić commit+push.

Aby uruchomić agenta: `@auto-agent [zadanie]`

## Struktura testów Taurus

- `test-api.yml` — standardowy test API (JSONPlaceholder)
- `test-advanced.yml` — zaawansowany test z większą konfiguracją
- `test-support.yml` — środowisko Support/Produkcja
- `test-locust.yml` — test z Locust
- Tryby uruchomienia: `health`, `standard`, `jmeter-java8`, `pipeline`

## BlazeMeter

- Dashboard: https://a.blazemeter.com/app/#/accounts/2190559/workspaces/2269510/dashboard
- Projekt: `repo-gotowe`
- Konfiguracja (poza repo): `~/.bzt-rc`
