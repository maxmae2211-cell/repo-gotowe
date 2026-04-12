## Podstawowe pojęcia Taurus

### Scenariusz (Scenario)
Definicja testu - co ma być testowane. Zawiera sekwencję requestów HTTP, skryptów czy akcji.

### Execution
Sposób uruchomienia scenariusza. Definiuje:
- `concurrency` - ile użytkowników symulujemy
- `hold-for` - jak długo trwa test
- `ramp-up` - czas acelacji (rozwijania obciążenia)
- `throughput` - liczba requestów/sekundę

### Przykład:
```yaml
execution:
  - concurrency: 10      # 10 użytkowników
    hold-for: 2m         # przez 2 minuty
    ramp-up: 30s         # rozwijamy przez 30 sekund
    scenario: my_test    # scenariusz do uruchomienia
```

### Profil obciążenia

#### Constant Load (Stałe obciążenie)
```yaml
concurrency: 10
hold-for: 2m
```

#### Ramp-up (Gradual increase)
```yaml
concurrency: 10
ramp-up: 30s    # od 0 do 10 użytkowników w 30s
hold-for: 1m    # potem trzymaj przez 1 minutę
```

#### Step Load (Krokowe obciążenie)
```yaml
concurrency:
  - 5     # 5 użytkowników
  - 10    # potem 10
  - 15    # potem 15
hold-for: 30s
```

### Metryki wydajności

Taurus raportuje:
- **Response Time** - średni czas odpowiedzi
- **Throughput** - liczba requestów/sekundę
- **Error Rate** - procent błędów
- **p95, p99** - percentyle czasu odpowiedzi

### Asercje (Assertions)

Weryfikacja poprawności odpowiedzi:
```yaml
requests:
  - url: https://api.example.com/status
    assertions:
      - contains:
          - 200
      - not-contains:
          - error
```

### Zmienne

Można definiować zmienne w konfiguracji:
```yaml
variables:
  base_url: https://api.example.com
  user_id: 123
  
requests:
  - url: ${base_url}/users/${user_id}
```

## Tryby testowania

1. **Functional Testing** - czy aplikacja działa poprawnie
2. **Performance Testing** - jaka jest wydajność
3. **Load Testing** - zachowanie pod ciężkim obciążeniem
4. **Stress Testing** - punkt zerwania systemu

## Raportowanie

Po uruchomieniu testu Taurus generuje:
- Konsola z live statusem
- HTML report w folder `.taurus`
- JTL (Java Test Log) format dla dalszej analizy
