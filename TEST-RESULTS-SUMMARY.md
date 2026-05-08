# Podsumowanie wyników testów Taurus - 8 maja 2026

## Status ogólny
✅ **Wszystkie testy uruchomione pomyślnie z działającym mock API serverem**

---

## 1. Test Load (test-api-load.yml)
**Czas wykonania**: 1:18 (78 sekund)  
**Status**: ✅ ZAKOŃCZONY POMYŚLNIE

### Metryki
- **Liczba próbek**: 4400
- **Failure rate**: 0.00% ✅
  - Get Request: 100% sukces
  - Create Post: 100% sukces
- **Średni czas odpowiedzi**: 0.136s
- **Latency**: 0.136s
- **Connect time**: 0.000s

### Percentyle czasów odpowiedzi
| Percentyl | Czas (s) |
|-----------|----------|
| p0        | 0.018    |
| p50       | 0.098    |
| p90       | 0.225    |
| p95       | 0.340    |
| p99       | 0.838    |
| p99.9     | 1.230    |
| p100      | 1.390    |

### Artefakty
- Katalog: `2026-05-08_23-59-04.142977`

---

## 2. Test Spike (spike.yml)
**Czas wykonania**: 0:44 (44 sekund)  
**Status**: ✅ ZAKOŃCZONY POMYŚLNIE (0% FAILURES)

### Metryki
- **Liczba próbek**: 443
- **Failure rate**: 0.00% ✅
- **Średni czas odpowiedzi**: 3.060s
- **Latency**: 3.060s
- **Connect time**: 0.046s

### Percentyle czasów odpowiedzi
| Percentyl | Czas (s) |
|-----------|----------|
| p0        | 0.01     |
| p50       | 1.594    |
| p90       | 7.536    |
| p95       | 7.748    |
| p99       | 8.368    |
| p99.9     | 8.416    |
| p100      | 8.416    |

### Obserwacje
- Test symuluje nagły wzrost obciążenia (1→200→1 wątków)
- Wszystkie requesty przeszły pomyślnie
- Wyższe średnie czasy ze względu na peak load
- System obsługuje spike bez problemów

### Artefakty
- Katalog: `2026-05-08_23-25-21.396966`

---

## 3. Test Soak (soak.yml)
**Czas wykonania**: 0:10:24  
**Status**: ✅ ZAKOŃCZONY POMYŚLNIE (0% FAILURES)

### Metryki
- **Liczba próbek**: 63367
- **Failure rate**: 0.00% ✅
- **Średni czas odpowiedzi**: 0.094s
- **Latency**: 0.094s
- **Connect time**: 0.000s

### Percentyle czasów odpowiedzi
| Percentyl | Czas (s) |
|-----------|----------|
| p0        | 0.006    |
| p50       | 0.069    |
| p90       | 0.152    |
| p95       | 0.222    |
| p99       | 0.594    |
| p99.9     | 1.004    |
| p100      | 1.355    |

### Artefakty
- Katalog: `2026-05-08_23-31-01.235709`

---

## 4. Test Assertions (assertions.yml)
**Czas wykonania**: 0:00:35  
**Status**: ✅ ZAKOŃCZONY POMYŚLNIE PO POPRAWCE KONFIGURACJI

### Metryki
- **Liczba próbek**: 1951
- **Failure rate**: 0.00% ✅
- **Średni czas odpowiedzi**: 0.050s

### Uwaga
- Wcześniejsza wersja asercji używała niepoprawnego formatu `condition/value`.
- Naprawiono na składnię Taurusa `contains: [200]` dla `subject: http-code`.

### Artefakty
- Katalog: `2026-05-08_23-53-08.677711`

---

## 5. Test SLA (test-api-sla.yml)
**Czas wykonania**: 0:02:17  
**Status**: ✅ ZAKOŃCZONY POMYŚLNIE (0% FAILURES)

### Metryki
- **Liczba próbek**: 11793
- **Failure rate**: 0.00% ✅
- **Średni czas odpowiedzi**: 0.050s
- **P95**: 0.122s
- **P99**: 0.329s

### Request labels
- `Get All Posts`: 100% sukces, avg 0.051s
- `Get Post 1`: 100% sukces, avg 0.050s

### Artefakty
- Katalog: `2026-05-08_23-44-46.073165`

---

## 6. Test JMeter CRUD (test-api-jmeter.yml)
**Czas wykonania**: 0:04:17  
**Status**: ✅ ZAKOŃCZONY POMYŚLNIE (0% FAILURES)

### Metryki
- **Liczba próbek**: 26262
- **Failure rate**: 0.00% ✅
- **Średni czas odpowiedzi**: 0.200s
- **P95**: 0.473s
- **P99**: 1.083s

### Request labels
- `Create Post`: 100% sukces, avg 0.200s
- `Get Created Post`: 100% sukces, avg 0.201s
- `Update Created Post`: 100% sukces, avg 0.200s
- `Delete Created Post`: 100% sukces, avg 0.199s

### Artefakty
- Katalog: `2026-05-08_23-47-40.162256`

---

## 7. Test K6 (test-api-k6.js)
**Czas wykonania**: 2m20s (+ graceful stop)  
**Status**: ✅ ZAKOŃCZONY POMYŚLNIE

### Metryki
- **Checks**: 1789/1789 (100.00%)
- **HTTP failures**: 0.00%
- **Średni czas `http_req_duration`**: 11.22ms
- **P90**: 13.55ms
- **P95**: 22.78ms
- **Maks. VUs**: 20

---

## Pozostałe dostępne testy
- `test-api-load.yml` - test obciążenia mieszanego GET/POST
- `spike.yml` - test skoku ruchu

---

## Wnioski
1. ✅ Mock API server działa stabilnie na localhost:8000
2. ✅ Taurus 1.16.50 prawidłowo konfigurowany
3. ✅ Infrastruktura testowa operacyjna
4. ✅ System obsługuje normalne obciążenie (load test)
5. ✅ System obsługuje spike'i bez problemów (spike test)
6. ✅ System stabilny w długim okresie (soak: 63k próbek, 0% błędów)
7. ✅ Workflow CRUD działa poprawnie pod obciążeniem (JMeter)
8. ✅ Testy SLA i K6 zakończone bez błędów
9. ✅ Problem `Create Post` (422) usunięty przez ustawienie `Content-Type: application/json` w scenariuszu load

## Rekomendacje
- [ ] Ujednolicić payload `Create Post` między scenariuszami
- [ ] Dodać test regresji asercji dla `http-code`
- [ ] Rozszerzyć testy o scenariusze failure resilience
