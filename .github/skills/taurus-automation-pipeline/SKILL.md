---
name: taurus-automation-pipeline
description: "Automatyzuje kolejne etapy Taurus na Windows: health check, standard run, JMeter+Java8 run, aktualizacja dokumentacji, walidacja, commit i push. Use when: dalej, next step, wykonuj nastepny etap automatycznie, zapisuj sam pliki, taurus pipeline, bzt workflow, runbook sync."
argument-hint: "Podaj cel etapu, np. validate and publish, oraz opcjonalnie config: test-api.yml"
user-invocable: true
---

# Taurus Automation Pipeline

## Co robi ta umiejetnosc
Ta umiejetnosc prowadzi powtarzalny workflow operacyjny Taurus od stanu repo do opublikowanych zmian, bez przerywania w polowie.

## Kiedy uzywac
- Gdy uzytkownik prosi o "dalej" i oczekuje nastepnego etapu automatycznie.
- Gdy trzeba zapisac pliki samodzielnie i od razu publikowac zmiany.
- Gdy trzeba utrzymac zgodnosc miedzy skryptami, taskami VS Code i runbookiem.

## Wejscie
- Domyslny config Taurus: test-api.yml
- Opcjonalny config: inny plik YAML przekazany przez uzytkownika
- Zakres: workspace project

## Procedura
1. Ustal stan startowy
- Uruchom `git status --short`, sprawdz branch i HEAD.
- Odczytaj aktualne pliki operacyjne: `scripts/run-taurus.ps1`, `.vscode/tasks.json`, `RUNBOOK-TAURUS.md`.

2. Wykonaj szybka walidacje
- Uruchom `./scripts/run-taurus.ps1 -Mode health`.
- Jesli health failuje, napraw przyczyne (sciezki, zaleznosci, config) przed dalszymi krokami.

3. Wykonaj etap funkcjonalny
- Dla biezacego scenariusza uruchom: `standard` albo `jmeter-java8` albo `pipeline`.
- Traktuj warning update-check 5xx jako nieblokujacy.

4. Synchronizuj artefakty operacyjne
- Jesli zmieniono logike uruchomien, zaktualizuj rownolegle: `scripts/run-taurus.ps1`, `.vscode/tasks.json`, `RUNBOOK-TAURUS.md`.
- Utrzymuj jeden zrodlowy workflow i te same nazwy trybow.

5. Obsluga decyzji i branching
- Jesli terminal ma szum lub PSReadLine blad: przerwij ten terminal, uruchom swieza sesje sync i powtorz walidacje.
- Jesli brakuje Java8 lub JMeter: zatrzymaj etap `jmeter-java8`, napraw zaleznosci i powtorz walidacje.
- Jesli pojawiaja sie niepowiazane zmiany uzytkownika: nie cofaj ich i commituj tylko pliki etapu.

6. Kryteria ukonczenia etapu
- Komendy walidacyjne koncza sie kodem 0.
- Taurus run ma 0.00% failures lub jasno udokumentowany wyjatek.
- `git status --short` po pushu jest pusty (dla plikow etapu).
- Zmiany sa wypchniete na poprawna galaz.

7. Publikacja
- `git add` tylko zmienione pliki etapu.
- Jeden czytelny commit opisujacy efekt.
- `git push origin <branch>`.
- Na koniec podaj: co zrobiono, commit SHA i stan repo.

## Jakosc i bezpieczenstwo
- Nie uzywaj destrukcyjnych komend git.
- Nie resetuj cudzych zmian.
- Przy bledach terminala preferuj nowe sesje sync zamiast kontynuacji uszkodzonego prompta.

## Wynik
Efektem jest domkniety etap: zweryfikowany workflow Taurus, zaktualizowane pliki operacyjne, commit oraz push bez recznego prowadzenia.
