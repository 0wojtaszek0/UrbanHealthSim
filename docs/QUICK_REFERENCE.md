# KARTA SZYBKIEGO ODNIESIENIA: Aplikacja Czynników Ryzyka

## 🚀 URUCHOMIENIE

```bash
streamlit run interactive_simulation_app.py
```

Aplikacja otworzy się w przeglądarce na: `http://localhost:8501`

---

## 🎮 INTERFEJS - CO ZNAJDUJE SIĘ W PANELU BOCZNYM (LEWY BOK)

### 📊 Ustawienia Populacji
| Parametr | Zakres | Default | Znaczenie |
|----------|--------|---------|-----------|
| Rozmiar populacji | 1K - 100K | 50K | Liczba agentów do symulacji |
| Czas symulacji | 5 - 50 lat | 50 | Jak długo symulować |
| Fertility multiplier | 0.5 - 2.5 | 1.0 | Mnożnik na wskaźnik urodzeń |
| Mortality multiplier | 0.3 - 2.0 | 1.0 | Mnożnik na wskaźnik śmiertelności |

### ⚠️ Suwaki Czynników Ryzyka (7 sztuk)

```
Mnożnik   |  Znaczenie
----------|------------------------------------------
0.0       |  Brak czynnika (eliminacja)
0.5       |  Zmniejszenie o 50%
1.0       |  Baseline - normalna populacja
1.5       |  Wzrost o 50%
2.0       |  Podwojenie prevalencji
3.0       |  Potrojenie
```

**7 Czynników Ryzyka:**
1. 🚬 **Smoking** (Palenie)
2. ⚖️ **Obesity** (Otyłość)
3. 🚫 **Physical Inactivity** (Brak aktywności)
4. 🍺 **Alcohol Abuse** (Nadużywanie alkoholu)
5. 🍔 **High Cholesterol** (Wysoki cholesterol)
6. 💊 **Hypertension Stage 0** (Nadciśnienie)
7. 👨‍👩‍👧 **Family History** (Historia rodzinna)

### 📋 Gotowe Scenariusze

Kliknij na dropdown aby wczytać preset:

- **Custom** - Ręczne dostrajanie
- **Healthy Population** - Wszystkie RF = 0.5
- **High-Risk** - Wszystkie RF = 1.5
- **Intervention (Best Case)** - Mieszany scenariusz optymistyczny

---

## 📊 WYNIKI - CO OTRZYMASZ PO SYMULACJI

### 1️⃣ Metryki Podsumowania (4 karty u góry)

```
┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  ┌─────────────┐
│ Initial Popul.  │  │ Final Popul.    │  │ Survival %   │  │ Average Age │
│ np. 50,000      │  │ np. 48,500      │  │ np. 97.0%    │  │ np. 48.5 yrs│
└─────────────────┘  └─────────────────┘  └──────────────┘  └─────────────┘
```

### 2️⃣ Piramida Wieku

- Interaktywna wizualizacja
- Niebieskie paski = Mężczyźni (od lewej)
- Czerwone paski = Kobiety (od prawej)
- Hover = Dokładne liczby

### 3️⃣ Prevalencja Chorób

Procent populacji z:
- **CVD** (Choroby serca i naczyń)
- **Lung Cancer** (Rak płuc)

### 4️⃣ Wpływ Czynników Ryzyka

Wykres słupkowy pokazujący który RF ma największy wpływ na choroby.

### 5️⃣ Trendy Populacji w Czasie

Liniowy wykres pokazujący populację rok po roku przez 50 lat.

### 6️⃣ Tabela Szczegółowych Statystyk

Kompletna tabela z:
- Deaths, Births
- CVD cases, Lung Cancer cases
- Multimorbidity %

### 7️⃣ Ustawienia Czynników Ryzyka

Podsumowanie wszystkich mnożników, które użyto.

### 8️⃣ Export Wyników

Przycisk do pobrania JSON z parametrami i wynikami.

---

## 💡 SCENARIUSZE DO PRZETESTOWANIA

### Scenario 1: Kampania Przeciw Paleniu

```
Smoking: 0.3
Inne: 1.0 (baseline)
```

**Spodziewany wynik:** ⬇️ Rak płuc, ⬇️ CVD, ⬆️ Przeżycie

### Scenario 2: Interwencja Lifestylowa

```
Smoking: 0.8
Obesity: 0.7
Physical Inactivity: 0.6
Cholesterol: 0.8
Hypertension: 0.7
Alcohol: 0.9
Family History: 1.0 (nie da się zmienić)
```

**Spodziewany wynik:** ⬆️ Zdrowsza populacja, ⬆️ Większa populacja końcowa

### Scenario 3: Populacja Wysokiego Ryzyka

```
Wszystkie RF: 1.5-2.0
```

**Spodziewany wynik:** ⬆️ Choroby, ⬇️ Przeżycie, ⬇️ Populacja końcowa

### Scenario 4: Ekstrema

```
Test 1: Wszystkie RF = 0.0
Test 2: Wszystkie RF = 3.0
```

**Obserwacja:** Jak zmienia się populacja przy skrajnych wartościach.

---

## 📈 CZYTANIE WYNIKÓW

### Survival Rate

```
Survival % = (Final Pop / Initial Pop) × 100%

Interpretacja:
- >90%  = Dobra (norma dla 50 lat)
- 80-90% = Wysoka śmiertelność
- <80%  = Problematyczne (czek multipliers)
```

### Disease Prevalence

```
Prevalencja = (Chorych / Populacji) × 100%

Typowe wartości:
- CVD: 20-40% (zależy od RF)
- Lung Cancer: 1-10% (mocno zależy od palenia)
```

### Population Trend

```
Wzrost > 0%   → Populacja rośnie (fertility > mortality)
Wzrost ≈ 0%   → Stabilna
Wzrost < -5%  → Populacja spada (mortality zbyt wysoka)
```

---

## ⏱️ CZASY WYKONANIA

```
Rozmiar      Years    Oczekiwany czas
─────────────────────────────────────
1,000        5        ~10 sec
5,000        10       ~20 sec
10,000       10       ~30 sec
50,000       50       90-120 sec
100,000      50       3-4 min
```

---

## 🔧 TROUBLESHOOTING

### ❌ Aplikacja nie startuje

```bash
# 1. Sprawdź Streamlit
pip3 show streamlit

# 2. Spróbuj zainstalować
pip3 install --break-system-packages streamlit

# 3. Uruchom demo zamiast
python3 demo_risk_factors.py
```

### ❌ Simulation timeout

- Zmniejsz rozmiar populacji (do 10K)
- Zmniejsz lata (do 20)
- Uruchom na mniejszym scenariuszu

### ❌ Liczby wydają się nierealne

- Sprawdź fertility/mortality multipliers (powinne być ~1.0)
- Zmniejsz RF multipliers (max 2.0 dla testów)
- Przeczytaj RISK_FACTORS_DOCUMENTATION.md

### ❌ Wykresy się nie pokazują

- Poczekaj na koniec symulacji
- Sprawdź konsolę pod błędami
- Odśwież przeglądarkę (F5)

---

## 💾 EKSPORT DANYCH

### JSON Export

Zawiera:
- Timestamp
- Wszystkie parametry
- Kluczowe wyniki
- Gotowy do dalszej analizy

```bash
# Po pobraniu JSON
cat simulation_results_*.json | python3 -m json.tool
```

### Screenshot Wyników

Użyj narzędzia screenshot przeglądarki (⌘+Shift+3 na Mac)

---

## 📚 GDZIE SZUKAĆ WIĘCEJ INFORMACJI

| Pytanie | Plik |
|---------|------|
| Jak działa Cox model? | RISK_FACTORS_DOCUMENTATION.md |
| Jakie są Hazard Ratios? | RISK_FACTORS_DOCUMENTATION.md |
| Jak użyć aplikacji? | README_INTERACTIVE_APP.md |
| Problemy? | README_INTERACTIVE_APP.md - Troubleshooting |
| Ogólne info | PODSUMOWANIE_RF_APP.md |

---

## 🎯 KLUCZOWE LICZBY DO ZAPAMIĘTANIA

**Hazard Ratios (wzrostowe ryzyka):**
- Smoking → Lung Cancer: **15×** (dominujący!)
- Smoking → CVD: **2.5×**
- Obesity → CVD: **1.7×**
- Hypertension → CVD: **2.2×**
- Cholesterol → CVD: **2.0×**

**Parametry populacji:**
- Default rozmiar: **50,000** agentów
- Default lata: **50** lat
- Default fertility: **1.0** (baseline)
- Default mortality: **1.0** (baseline)

**RF Multipliers:**
- Min: **0.0** (eliminacja)
- Baseline: **1.0**
- Max: **3.0** (potrojenie)

---

## ✅ CHECKLIST PRZED URUCHOMIENIEM

- [ ] Python 3 zainstalowany
- [ ] `pip3 install -r requirements.txt` (z Streamlit)
- [ ] Jesteś w folderze `/04.05.2026`
- [ ] Przeglądarka otwarta
- [ ] Masz 2 minuty na czekanie (dla 50K/50lat)

---

## 🚀 GOTOWY? START!

```bash
cd /Users/wojciechofiara/Desktop/04.05.2026
streamlit run interactive_simulation_app.py
```

Powodzenia! 🎉

---

**Szybki reference - drukuj lub zapisz jako bookmark!**
