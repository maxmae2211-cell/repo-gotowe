# Taurus — Instrukcja Obsługi (Język Polski)

> **Taurus** to narzędzie do testów wydajnościowych API, stron WWW i usług sieciowych.
> Pozwala symulować setki lub tysiące użytkowników jednocześnie i mierzyć czas odpowiedzi serwera.

---

## Spis treści

1. [Co to jest Taurus?](#1-co-to-jest-taurus)
2. [Jak uruchomić test?](#2-jak-uruchomić-test)
3. [Co się dzieje podczas testu?](#3-co-się-dzieje-podczas-testu)
4. [Jak czytać wyniki?](#4-jak-czytać-wyniki)
5. [Kiedy test się nie powiedzie?](#5-kiedy-test-się-nie-powiedzie)
6. [Jak zmienić testowany adres URL?](#6-jak-zmienić-testowany-adres-url)
7. [Jak uruchomić test na środowisku support?](#7-jak-uruchomić-test-na-środowisku-support)
8. [Tryby uruchomienia](#8-tryby-uruchomienia)
9. [Kody błędów](#9-kody-błędów)
10. [Najczęstsze problemy](#10-najczęstsze-problemy)

---

## 1. Co to jest Taurus?

Taurus (narzędzie open source) symuluje **wielu użytkowników** wysyłających żądania do serwera w tym samym czasie.

**Przykład:** Chcesz sprawdzić czy Twoja aplikacja wytrzyma 50 użytkowników jednocześnie przez 2 minuty.  
Taurus to uruchomi i powie Ci:

- Ile żądań na sekundę obsłużył serwer
- Jaki był średni czas odpowiedzi (np. 200ms)
- Ile żądań się nie powiodło (błędy)

---

## 2. Jak uruchomić test?

### Opcja A — przez VS Code (zalecane)

1. Otwórz VS Code
2. Naciśnij `Ctrl+Shift+P`
3. Wpisz `Tasks: Run Task`
4. Wybierz jedno z zadań Taurusa:

| Nazwa zadania | Co robi |
|---|---|
| **Taurus: Kontrola zdrowia** | Sprawdza czy Taurus jest prawidłowo zainstalowany |
| **Taurus: Standardowy test API** | Uruchamia test na demo API |
| **Taurus: Test środowiska Support/Produkcja** | Uruchamia test na API support/produkcji |
| **Taurus: Pelny potok** | Kontrola zdrowia + test standardowy + test JMeter |
| **Taurus: JMeter + Java8** | Test z silnikiem JMeter (zamiast domyślnego) |

### Opcja B — przez terminal PowerShell

```powershell
# Przejdź do katalogu projektu
cd c:\Users\maxma\Documents\GitHub\repo-gotowe

# Kontrola zdrowia (czy Taurus działa)
.\scripts\run-taurus.ps1 -Mode health

# Standardowy test API
.\scripts\run-taurus.ps1 -Mode standard

# Test środowiska support/produkcja
.\scripts\run-taurus.ps1 -Mode standard -Config test-support.yml

# Pełny potok (wszystkie kroki)
.\scripts\run-taurus.ps1 -Mode pipeline
```

---

## 3. Co się dzieje podczas testu?

Gdy uruchomisz test, zobaczysz w konsoli tabelę aktualizowaną co kilka sekund:

```
+----+--------+--------+--------+------+---------+--------+
| Conc |  Avg | Perc 90 | Perc 95 | OK  | Fail    | Err %  |
+----+--------+--------+--------+------+---------+--------+
|  10 | 245ms |  320ms  |  380ms  | 150 | 0       | 0.00%  |
+----+--------+--------+--------+------+---------+--------+
```

**Co oznaczają kolumny:**

| Kolumna | Znaczenie |
|---|---|
| `Conc` | Liczba jednoczesnych użytkowników (concurrency) |
| `Avg` | Średni czas odpowiedzi serwera |
| `Perc 90` | 90% żądań trwało krócej niż ta wartość |
| `Perc 95` | 95% żądań trwało krócej niż ta wartość |
| `OK` | Liczba udanych żądań |
| `Fail` | Liczba nieudanych żądań |
| `Err %` | Procent błędów |

**Dobry wynik:** `Err %` = 0.00%, `Avg` poniżej 1 sekundy.

Po zakończeniu testu **automatycznie otworzy się raport HTML** w przeglądarce z wykresami.

---

## 4. Jak czytać wyniki?

### Raport HTML (otwiera się automatycznie)

Po każdym teście w przeglądarce otworzy się raport z:

- Wykresem czasu odpowiedzi w czasie
- Wykresem przepustowości (żądań/s)
- Tabelą percentyli (p50, p90, p95, p99)
- Listą błędów

### Wynik końcowy w konsoli

Na końcu testu zobaczysz podsumowanie:

```
Request label   | # reqs | avg  | min  | max   | err%
Get Post 1      |   120  | 245  |  80  |  850  | 0.00%
Create Post     |   118  | 312  | 100  | 1200  | 0.00%
```

### Pliki wynikowe

Taurus tworzy katalog z datą i godziną (np. `2026-05-02_10-30-00.123456/`) zawierający:

- `report.html` — raport HTML z wykresami
- `bzt.log` — szczegółowy dziennik (do diagnostyki błędów)
- `kpi.jtl` — surowe dane wynikowe

---

## 5. Kiedy test się nie powiedzie?

Test automatycznie się zatrzyma jeśli wystąpi jeden z warunków:

| Warunek | Znaczenie |
|---|---|
| Więcej niż **10% błędów** przez 30 sekund | Serwer odpowiada błędami zbyt często |
| Średni czas odpowiedzi **powyżej 5 sekund** przez 30 sekund | Serwer odpowiada zbyt wolno |

Kod wyjścia `3` oznacza że test zatrzymał się z powodu niespełnienia kryteriów.

---

## 6. Jak zmienić testowany adres URL?

Edytuj plik `test-api.yml`:

```yaml
scenarios:
  api_test:
    requests:
      - url: https://TWOJ-ADRES-API/endpoint   # <-- zmień tutaj
        label: Moj test
        method: GET
```

Zapisz plik i uruchom test ponownie.

---

## 7. Jak uruchomić test na środowisku support?

1. Otwórz plik `test-support.yml`
2. Zamień adresy URL z `https://support-api.example.com/...` na rzeczywiste adresy Twojego środowiska support
3. Uruchom:

```powershell
.\scripts\run-taurus.ps1 -Mode standard -Config test-support.yml
```

Lub w VS Code: `Ctrl+Shift+P` → `Tasks: Run Task` → **"Taurus: Test środowiska Support/Produkcja"**

---

## 8. Tryby uruchomienia

| Tryb (`-Mode`) | Opis |
|---|---|
| `health` | Kontrola zdrowia — sprawdza instalację Taurusa, nie uruchamia testów |
| `standard` | Standardowy test API — uruchamia scenariusz z pliku konfiguracyjnego |
| `jmeter-java8` | Test z silnikiem JMeter + Java 8 — bardziej szczegółowe statystyki |
| `pipeline` | Pełny potok — wykonuje health + standard + jmeter-java8 po kolei |

**Parametr `-Config`** pozwala wybrać inny plik konfiguracyjny (domyślnie `test-api.yml`):

```powershell
.\scripts\run-taurus.ps1 -Mode standard -Config test-support.yml
.\scripts\run-taurus.ps1 -Mode standard -Config test-advanced.yml
```

---

## 9. Kody błędów

| Kod | Znaczenie | Co zrobić |
|---|---|---|
| `0` | ✅ Test zakończony sukcesem | Nic — wszystko OK |
| `1` | ❌ Błąd ogólny (sieć, konfiguracja) | Sprawdź `bzt.log` w katalogu wynikowym |
| `2` | ⚠️ Test zatrzymany ręcznie (Ctrl+C) | Normalne — sam/a zatrzymałeś/aś test |
| `3` | ❌ Kryteria pass/fail nie spełnione | Serwer jest zbyt wolny lub generuje błędy |

---

## 10. Najczęstsze problemy

### Problem: "Nie znaleziono pliku wykonywalnego bzt"

**Rozwiązanie:** Zainstaluj Taurus ponownie przez VS Code:

- `Ctrl+Shift+P` → `Tasks: Run Task` → **"Windows: Zainstaluj wymagania systemowe"**
- Następnie `F5` → **"Debug: Taurus krok 1"**, **"krok 2"**, **"krok 3"**

### Problem: Test kończy się błędem "setuptools"

**Rozwiązanie:** Uruchom w terminalu:

```powershell
C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe -m pip install setuptools==79.0.1
```

### Problem: Raport HTML nie otwiera się

**Rozwiązanie:** Otwórz ręcznie — znajdź w katalogu projektu folder z datą (np. `2026-05-02_10-30-00.123456`) i otwórz plik `report.html`.

### Problem: Test zwraca dużo błędów na środowisku support

**Możliwe przyczyny:**

- Nieprawidłowe adresy URL w `test-support.yml`
- Serwer wymaga autoryzacji (nagłówek `Authorization`)
- Zbyt duże obciążenie (zmniejsz `concurrency` w pliku konfiguracyjnym)

---

## Szybki przewodnik — pierwsze kroki

```
1. Otwórz VS Code
2. Ctrl+Shift+P → Tasks: Run Task
3. Wybierz "Taurus: Kontrola zdrowia" → sprawdź czy działa
4. Wybierz "Taurus: Standardowy test API" → uruchom test
5. Po zakończeniu otworzy się raport HTML w przeglądarce
```

---

*Dokumentacja wygenerowana automatycznie dla środowiska Windows. Wersja Taurus: 1.16.50*
