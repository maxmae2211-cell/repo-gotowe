# Lokalny test Azure Functions przez Taurus

Scenariusz [test-local-function.yml](test-local-function.yml) testuje
`GET http://127.0.0.1:7071/api/httpTrigger1?name=Taurus`.
Uzywa 5 uzytkownikow, docelowo 10 zadan/s, z narastaniem przez 10 sekund
i obciazeniem przez kolejne 30 sekund. Limit czasu zadania wynosi 5 sekund.
Narastanie, uruchamianie JMeter i zamykanie testu wplywaja na calkowity czas
oraz liczbe zadan; 10 zadan/s jest celem, nie gwarantowanym wynikiem.

## Wymagania i uruchomienie aplikacji

- Node.js, zaleznosci z `package.json` i Azure Functions Core Tools v4.
- Zainstalowany Azurite.
- Srodowisko Taurus obslugiwane przez
  [scripts/run-taurus.ps1](scripts/run-taurus.ps1), Python i Java dla JMeter.
- W lokalnym, ignorowanym przez Git `local.settings.json`, w sekcji `Values`:
  `AzureWebJobsStorage` ustawione na `UseDevelopmentStorage=true`
  i `FUNCTIONS_WORKER_RUNTIME` ustawione na `node`.
  Nie dodawaj connection stringow ani kluczy do repozytorium.

W terminalu **PowerShell** uruchom Azurite i pozostaw go dzialajacego:

```powershell
azurite --location "$env:LOCALAPPDATA\Azurite\repo-gotowe"
```

Emulator powinien nasluchiwac lokalnie na portach 10000, 10001 i 10002.
W drugim terminalu, w katalogu repozytorium:

```powershell
npm run start
```

Host powinien udostepniac funkcje na porcie 7071.
Jesli port jest zajety, sprawdz istniejacy host zamiast uruchamiac kolejny.
Po zmianie `local.settings.json` zrestartuj host, aby odczytal konfiguracje.
Ta funkcja korzysta z Node.js; aktywacja Python `.venv` nie jest potrzebna
do uruchomienia hosta.

Sprawdz odpowiedz przed testem:

```powershell
Invoke-RestMethod 'http://127.0.0.1:7071/api/httpTrigger1?name=Taurus'
```

Oczekiwana odpowiedz: `Hello, Taurus!`.
Powyzsze polecenia sa dla PowerShell, nie CMD.

## Uruchomienie testu przez AI lub automatyzacje

Zgodnie z [runbookiem](RUNBOOK-TAURUS.md) testy Taurus uruchamia AI lub
automatyzacja, wylacznie przez istniejacy runner:

```powershell
.\scripts\run-taurus.ps1 -Mode health -Config test-local-function.yml
.\scripts\run-taurus.ps1 -Mode standard -Config test-local-function.yml
```

Nie uruchamiaj bezposrednio `bzt` i nie dodawaj `-AllowParallel`.
Health check sprawdza narzedzia; nie uruchamia Azurite ani hosta Functions.
Scenariusz dziala lokalnie i nie dodaje raportowania do BlazeMeter.
Taurus nadal odczytuje ustawienia uzytkownika z `.bzt-rc`; pozostaw je
poza repozytorium.

## Wynik i interpretacja

Kazde zadanie musi zwrocic HTTP 200 i zawierac `Hello, Taurus!`.
Kryterium `failures>0` oznacza niepowodzenie testu przy dowolnym bledzie,
w tym bledzie asercji lub przekroczeniu limitu czasu.
Oczekiwany wynik: kod wyjscia 0 i dokladnie 0 bledow.

Runner zapisuje transkrypcje w `logs`, a Taurus zapisuje artefakty w folderze
z data uruchomienia. W `bzt.log` znajdziesz podsumowanie; `kpi.jtl` zawiera
probki JMeter. Oceniaj liczbe bledow, sredni czas, mediane i P95.
Test nie narzuca progu P95 i nie mierzy maksymalnej wydajnosci aplikacji.
Wynik lokalny obejmuje host, JMeter oraz obciazenie komputera i nie jest
prognoza wydajnosci w Azure.
