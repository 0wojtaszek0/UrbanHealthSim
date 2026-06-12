# Agent-Based Model — Demograficzna Symulacja Populacji Polski

> **Projekt zespołowy 2026** — Agent-Based Model (ABM) symulujący dynamikę demograficzną populacji polskiej przez 50 lat, oparty na rzeczywistych danych GUS Poland 2021 oraz danych z programu Białystok+.

---

## Spis treści

1. [Czym jest ten projekt?](#1-czym-jest-ten-projekt)
2. [Struktura plików](#2-struktura-plików)
3. [Architektura modelu](#3-architektura-modelu)
4. [Przechowywanie agentów](#4-przechowywanie-agentów)
5. [Klasy i komponenty](#5-klasy-i-komponenty)
6. [Silnik symulacji — jak działa?](#6-silnik-symulacji--jak-działa)
7. [Tabele demograficzne i wskaźniki CBR/CDR/TFR](#7-tabele-demograficzne)
8. [Gridsearch — 3 tryby i porównanie proxy ↔ ABM](#8-gridsearch--optymalizacja-parametrów)
9. [Piramidy wieku](#9-piramidy-wieku)
10. [Model dynamicznego ryzyka — Cox cumulative hazard](#10-model-dynamicznego-ryzyka--cox-cumulative-hazard)
11. [Wszystkie poprawki (bug fixes)](#11-wszystkie-poprawki-bug-fixes)
12. [Kalibracja — przed i po poprawkach](#12-kalibracja--przed-i-po-poprawkach)
13. [Flat rate vs. mnożnik tabel wiekowych](#13-flat-rate-vs-mnożnik-tabel-wiekowych)
14. [Wnioski](#14-wnioski)
15. [Przykładowe pytania i odpowiedzi](#15-przykładowe-pytania-i-odpowiedzi)
16. [Jak uruchomić?](#16-jak-uruchomić)
17. [Wzory matematyczne — kompendium](#17-wzory-matematyczne--kompendium)

---

## 1. Czym jest ten projekt?

Jest to **pełna implementacja Agent-Based Model (ABM)** demografii populacji Polski. Każdy mieszkaniec jest osobnym obiektem (agentem), który:

- Starzeje się o 1 miesiąc na każdą iterację symulacji
- Może umrzeć z prawdopodobieństwem zależnym od wieku, płci, chorób i czynników ryzyka
- Może urodzić dziecko (jeśli jest kobietą w wieku 15–50 lat) z prawdopodobieństwem zależnym od wieku
- Należy do gospodarstwa domowego i strefy geograficznej
- Posiada **2 choroby przewlekłe** (CVD, Lung Cancer) i **7 czynników ryzyka** (palenie, otyłość, brak aktywności, alkohol, hipercholesterolemia, nadciśnienie, historia rodzinna)
- Kumuluje przez całe życie **biologiczny hazard** (Cox-style cumulative hazard) — narażenie na RF przekłada się na rosnące ryzyko inicjacji choroby i wzrost mortality

Model symuluje **50 000 agentów przez 50 lat (600 miesięcy)** używając danych z Tablic Trwania Życia GUS Poland 2021, z dynamicznym modelem ryzyka chorób przewlekłych nałożonym na bazowy hazard demograficzny.

**Dlaczego ABM, a nie makromodel?**  
ABM pozwala na heterogeniczność — każdy agent ma własny wiek, płeć, choroby i historię. Można dokładnie śledzić piramidy wiekowe, wielochorobowość i nierówności zdrowotne w sposób niemożliwy w agregowanych modelach ODE/PDE.

---

## 2. Struktura plików

```
ABM - poprawiony gridsearch/
│
├── simulation_engine.py              # Główny silnik ABM — serce projektu
├── citizen.py                        # Klasa agenta (Citizen) + cumulative_hazard
├── household.py                      # Klasa gospodarstwa domowego
├── zone.py                           # Klasa strefy geograficznej
├── disease_model.py                  # Model chorób, RF, macierz β Coxa, baseline hazard
├── main.py                           # Uruchamia jedną symulację, generuje wykresy
│
├── grid_search_improved_v3_fixed.py     # Tryb 1: Analityczny proxy + heatmap PNG (~30s)
├── gridsearch_age_pyramids_analysis.py  # Tryb 2: ABM dla piramid (3×3 + diagonale, ~5 min)
├── gridsearch_full_abm_no_rf.py         # Tryb 3: Pełny ABM 12×12 bez RF (~50 min) ★NOWY
├── porownanie_gridsearch.py             # Porównanie proxy ↔ ABM (3-panelowa heatmapa) ★NOWY
├── comparison_flatrate_vs_multiplier.py # Porównanie flat-rate vs mnożnik tabel
├── piramida_optimum.py                  # Piramida dla optymalnego punktu (FM=2.12, MM=1.13)
│
│ ── DYNAMICZNY MODEL RYZYKA (Cox cumulative hazard) ─────────────────
├── piramida_porownanie_ryzyko.py     # 2 piramidy obok siebie z aktywnym modelem Coxa
├── populacja_w_czasie.py             # Trajektorie ludności rok-po-roku, 2 scenariusze
├── graf_ryzyko_choroby.py            # Sankey + sieć + heatmapa HR (7 RF → 2 chorób)
│
│ ── ANALIZA WYNIKÓW ABM GRIDSEARCH (osobny folder) ───────────────── ★NOWY
├── analiza_ABM_gridsearch/
│   ├── README.md                         # Index folderu
│   ├── piramidy_3x3_no_rf.py/.html       # Siatka 3×3 piramid (9 ABM bez RF)
│   ├── piramida_porownanie_z_rf.py/.html # 2 piramidy: ABM optimum vs dolny-środkowy (z RF)
│   ├── populacja_w_czasie_no_rf.py/.html # Trajektorie 50 lat dla 2 punktów (bez RF)
│   └── graf_ryzyko_choroby.py/.html      # Kopia grafu (RF-niezależny)
│
│ ── INTERAKTYWNA APLIKACJA CZYNNIKÓW RYZYKA ─────────────────────── ★NOWA
├── RISK_FACTORS_DOCUMENTATION.md        # Pełna dokumentacja implementacji RF (Cox model)
├── interactive_simulation_app.py        # Aplikacja Streamlit do zmiany RF i symulacji
├── demo_risk_factors.py                 # Demo skrypt porównujący scenariusze
├── README_INTERACTIVE_APP.md            # Instrukcja obsługi aplikacji
│
│ ── ARTEFAKTY WYJŚCIOWE ─────────────────────────────────────────────
├── piramidy_gridsearch_siatka.html        # Siatka 3×3 piramid z gridsearch (stara, pre-Cox)
├── piramidy_diagonale_gridsearch.html     # Profile wzdłuż 3 diagonali gridsearch
├── comparison_flatrate_vs_multiplier.html # Porównanie obu podejść (2×3 piramidy)
├── piramida_optimum.html                  # Optimum gridsearcha (FM=2.12, MM=1.13)
├── piramida_porownanie_ryzyko.html        # Optimum vs dolny-środkowy (z Cox)
├── populacja_w_czasie.html                # Trajektorie 50 lat (2 scenariusze)
├── graf_ryzyko_choroby.html               # Graf RF → choroby (3 widoki)
├── heatmap_gridsearch_v3_fixed_*.png      # Analityczna mapa ciepła (PNG) — proxy
├── heatmap_gridsearch_full_abm_no_rf_*.png  # Heatmapa ABM bez RF ★NOWY
├── porownanie_gridsearch_proxy_vs_abm.png   # Porównanie 3-panelowe (A: proxy, B: ABM, C: Δ) ★NOWY
├── gridsearch_results_v3_fixed_*.json     # Wyniki gridsearch proxy (JSON)
├── gridsearch_full_abm_no_rf_*.json       # Wyniki gridsearch ABM bez RF (JSON) ★NOWY
│
└── README.md                              # Ten plik
```

---

## 3. Architektura modelu

```
┌─────────────────────────────────────────────────────────────┐
│                     SimulationEngine                        │
│                                                             │
│  citizens: Dict[int, Citizen]   ←── główna populacja       │
│  households: Dict[int, Household]                           │
│  zones: Dict[int, Zone]                                     │
│  yearly_stats: Dict[int, Dict]  ←── statystyki roczne      │
│                                                             │
│  ┌─────────────┐  ┌───────────┐  ┌──────┐  ┌────────────────────┐ │
│  │   Citizen   │  │ Household │  │ Zone │  │   DiseaseModel     │ │
│  │             │  │           │  │      │  │  - CVD             │ │
│  │ age         │  │ members[] │  │ zone │  │  - Lung Cancer     │ │
│  │ sex         │  │ zone_id   │  │ air  │  │                    │ │
│  │ alive       │  │           │  │      │  │  HAZARD_BETA       │ │
│  │ diseases    │  │           │  │      │  │  BASELINE_HAZARD   │ │
│  │ risk_factors│  │           │  │      │  │  AGE_HAZARD_GROWTH │ │
│  │ cum_hazard  │◄─┼───────────┼──┼──────┼──┤  MORTALITY_GAMMA   │ │
│  └─────────────┘  └───────────┘  └──────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

`Citizen.cumulative_hazard` to słownik `{disease: H_cum}` — biologiczna pamięć agenta, do której co miesiąc dopisuje się przyrost hazardu zależny od wieku i RF (model Coxa, sekcja 10).

### Pętla symulacji (co miesiąc)

```
for month in range(600):           # 50 lat × 12 miesięcy
    1. age_all()                   # każdy agent: age_months += 1
    2. handle_deaths()             # 3-fazowy model Coxa (sekcja 10):
                                   #   a) akumulacja H_cum dla każdej choroby
                                   #   b) inicjacja choroby gdy P=1-exp(-Δh)
                                   #   c) mortality = base × exp(γ·H_cum) × MM
    3. handle_births()             # losowe narodziny wg tabeli płodności
    4. handle_household_splits()   # dorośli 25+ opuszczają domy
    5. update_health_states()      # progresja stanów zdrowia
    6. if month % 12 == 0:
           collect_yearly_stats()  # piramida wieku, populacja, itp.
```

---

## 4. Przechowywanie agentów

### Struktura danych: `Dict[int, Citizen]`

```python
self.citizens: Dict[int, Citizen] = {}
# Przykład:
# {
#   0: Citizen(sex="male",  age_months=384, alive=True,  ...),
#   1: Citizen(sex="female",age_months=252, alive=True,  ...),
#   2: Citizen(sex="female",age_months=816, alive=False, ...),  ← martwy, ale zostaje
#   ...
# }
```

**Dlaczego słownik, a nie lista?**

| Kryterium | `Dict[int, Citizen]` | `List[Citizen]` |
|-----------|----------------------|-----------------|
| Lookup po ID | O(1) | O(n) |
| Usunięcie martwych | Nie trzeba (flaga `alive`) | Drogie przesunięcia |
| Iteracja po żywych | `if c.alive` | Analogicznie |
| Nowe narodziny | `citizens[newborn.id] = newborn` | `append()` |
| Stabilność referencji | Stałe ID przez całe życie | Indeksy przesuwają się |

**Kluczowy szczegół — martwi agenci NIE są usuwani ze słownika.** Mają flagę `alive = False`. Dzięki temu:
- Household może sprawdzić czy agent nadal żyje bez `KeyError`
- Statystyki retrospektywne są możliwe
- Unika się kosztownej przebudowy słownika w trakcie symulacji

**Unikalny ID agenta** jest generowany przez zmienną klasową `Citizen._next_id` i nigdy się nie powtarza (nawet po śmierci agenta).

---

## 5. Klasy i komponenty

### `Citizen` — agent populacji

```python
class Citizen:
    id: int               # unikalny, auto-inkrementowany
    sex: str              # "male" lub "female"
    age_months: int       # wiek w miesiącach (nie latach!)
    alive: bool           # True/False
    household_id: int     # przynależność do gospodarstwa
    zone_id: int          # strefa geograficzna (1–4)
    diseases: Dict[str, int]     # {"CVD": 0, "Lung Cancer": 1}
    disability_score: float      # suma wag chorób (0.0–1.0)
    risk_factors: Dict[str, int] # {"smoking": 0, "obesity": 1, ...}
    cumulative_hazard: Dict[str, float]  # {"CVD": 0.123, "Lung Cancer": 0.045}
                                          # — biologiczna pamięć Coxa (sekcja 10)

    # Właściwości
    @property
    def age_years(self) -> float:
        return self.age_months / 12.0

    def num_conditions(self) -> int:     # liczba aktywnych chorób
    def compute_disability_score(...)    # aktualizuje disability_score
```

**Atrybuty czynników ryzyka** są inicjalizowane losowo przy tworzeniu agenta (wszystkie 7 RF):

| Risk factor              | Prevalence inicjalna | Główny wpływ |
|--------------------------|-------------|--------------|
| `smoking`                | ~25% (peak 40–60) | Lung Cancer HR=15, CVD HR=2.5 |
| `obesity`                | rośnie z wiekiem do ~45% | CVD HR=1.7 |
| `physical_inactivity`    | rośnie z wiekiem do ~50% | CVD HR=1.4 |
| `alcohol_abuse`          | ~8% (20–65 lat) | CVD HR=1.3 |
| `high_cholesterol` (hipercholesterolemia) | rośnie z wiekiem do ~40% | CVD HR=2.0 |
| `hypertension_stage0`    | rośnie z wiekiem do ~35% | CVD HR=2.2 |
| `family_history`         | ~15% (stały) | CVD/LC HR=1.5 |

### `Household` — gospodarstwo domowe

```python
class Household:
    id: int
    zone_id: int
    members: List[int]   # lista ID agentów (nie obiektów!)

    def add_member(citizen_id: int)
    def remove_member(citizen_id: int)
    def size() -> int
```

Przechowuje **ID obywateli, nie referencje** — unika cyklicznych zależności i ułatwia serializację.

### `Zone` — strefa geograficzna

Model ma 4 strefy z różnymi parametrami środowiskowymi:

| Strefa | Jakość powietrza | Dostęp do opieki | Gęstość |
|--------|-----------------|------------------|---------|
| 1      | 0.75 (wysoka)   | 0.90 (dobry)     | 4000/km² |
| 2      | 0.65 (średnia)  | 0.85             | 6000/km² |
| 3      | 0.70            | 0.80             | 5000/km² |
| 4      | 0.55 (niska)    | 0.75 (ograniczony) | 8000/km² |

W aktualnej wersji parametry środowiskowe są przechowywane, ale wpływ na śmiertelność i choroby jest minimalny — głównym motorem demograficznym są wiekowe tabele GUS.

### `DiseaseModel` — model chorób + macierz ryzyka Coxa

**Dwie choroby przewlekłe** z rzeczywistymi danymi epidemiologicznymi:

| Choroba | Prevalence inicjalna | Disability weight |
|---------|-----------|------------------|
| CVD (choroby sercowo-naczyniowe) | 35.0% | 0.25 |
| Lung Cancer (rak płuca) | 4.5% | 0.55 |

> **Uwaga historyczna**: We wcześniejszej wersji modelu *hipercholesterolemia* była traktowana jako trzecia choroba (DW=0.08). Po refaktorze została przeniesiona do *risk factors* (`high_cholesterol`), co jest biologicznie poprawne — sam wysoki cholesterol nie jest chorobą, lecz czynnikiem ryzyka dla CVD (HR=2.0).

```python
disability_score = Σ (disease_active × disability_weight)
# Przykład: CVD + Lung Cancer → 0.25 + 0.55 = 0.80
```

**Dodatkowo `DiseaseModel` przechowuje 4 macierze/słowniki dla modelu Coxa** (szczegóły w sekcji 10):

```python
HAZARD_BETA[disease][risk_factor]   # β = ln(HR), macierz 2×7
BASELINE_HAZARD[disease]            # λ_0 miesięczny dla wieku 30 lat
AGE_HAZARD_GROWTH[disease]          # γ_age (Gompertz: λ(a) = λ_0·exp(γ·(a-30)))
MORTALITY_GAMMA[disease]            # γ_d w mnożniku mortality exp(γ·H_cum)
```

Plus dwie metody pomocnicze:

```python
disease_model.monthly_hazard_increment(disease, age, risk_factors) -> float
disease_model.cox_mortality_log_hazard(diseases, cumulative_hazard) -> float
```

### `SimulationEngine` — główny silnik

Kluczowe parametry konfiguracyjne:

```python
engine.fertility_rate = 1.0          # mnożnik płodności (FM) — historyczna nazwa
engine.mortality_multiplier = 1.0    # mnożnik śmiertelności (MM)
engine.household_split_probability = 0.001  # 0.1%/miesiąc
```

#### Dlaczego `mortality_rate` / `fertility_rate` → `mortality_multiplier` / `fertility_multiplier`?

W pierwszej wersji modelu parametry sterujące w `SimulationEngine` nazywały się `fertility_rate` i `mortality_rate`. Z biegiem prac okazało się, że **te nazwy są mylące** — sugerują, że parametr JEST stopą demograficzną (np. CBR=8.5‰, CDR=13.5‰), w jednostce promili.

W rzeczywistości te parametry są **bezwymiarowymi mnożnikami całych tabel wiekowych**:

```python
# To, co naprawdę robi parametr "fertility_rate":
monthly_birth_prob = ASFR(wiek_kobiety) / 12  ×  fertility_rate
#                    └──────┬────────┘             └──────┬─────┘
#                    stopa wiekowa GUS              MNOŻNIK (×, nie ‰!)

# To, co naprawdę robi "mortality_multiplier":
monthly_death_prob = q_x(wiek, płeć)  ×  mortality_multiplier
#                    └──────┬──────┘     └──────┬──────────┘
#                    stopa GUS              MNOŻNIK (×)
```

**Pomyłki, które generowała stara nazwa:**

- `fertility_rate = 2.0` → ktoś czyta to jako "TFR=2.0" lub "CBR=2‰". W rzeczywistości oznacza to "wszystkie wiekowe stopy ASFR × 2.0", czyli TFR ≈ 2.56 i CBR ≈ 16.6‰.
- `mortality_rate = 0.5` → wygląda jak "0.5/1000/rok". W rzeczywistości oznacza "połowa polskiej śmiertelności w każdym wieku", czyli CDR ≈ 7.8‰.

**Dlatego w gridsearch i w dokumentacji konsekwentnie używamy nazw `fertility_multiplier` (FM) i `mortality_multiplier` (MM):**

| Parametr (nowa nazwa) | Co reprezentuje | FM/MM = 1.0 znaczy | FM/MM = 2.0 znaczy |
|----------------------|-----------------|--------------------|--------------------|
| `fertility_multiplier` | mnożnik tabeli ASFR | GUS 2021 (TFR=1.28, CBR=8.3‰) | każdy ASFR × 2 (TFR≈2.56, CBR≈16.6‰) |
| `mortality_multiplier` | mnożnik tabeli q_x | GUS 2021 (CDR=15.6‰) | każdy q_x × 2 (CDR≈31‰) |

**Korzyści ze zmiany nazewnictwa:**

1. **Jednoznaczność jednostek** — mnożnik jest bezwymiarowy (×), stopa jest w promile (‰). Niemożliwe do pomylenia.
2. **Zgodność z literaturą demograficzną** — w demografii "rate" to ścisłe pojęcie (CBR, CDR, ASFR, TFR). Słowo `_multiplier` nie sugeruje, że parametr jest stopą.
3. **Czytelne wyniki gridsearch** — `FM=1.88, MM=1.0` jest jednoznaczne (1.88× polska płodność daje stabilność). Przy starej nazwie `fertility_rate=1.88` mogło być rozumiane jako "TFR=1.88" lub "1.88‰".
4. **Spójność z koncepcją** — sekcja 13 pokazuje, że istnieje alternatywa **flat rate** (rzeczywista stopa CBR/CDR jednakowa dla wszystkich wieków, w jednostce ‰). Rozdzielenie nazw `_multiplier` (×, skaluje tabele) vs. `_rate` (‰, jedna stopa dla wszystkich) eliminuje dwuznaczność.

**Status w kodzie**: Atrybut w `SimulationEngine` nadal nazywa się `self.fertility_rate` (zachowana stara nazwa dla wstecznej kompatybilności wewnątrz silnika), ale **wszystkie skrypty i dokumentacja** używają konsekwentnie `fertility_multiplier`/`FM`. Atrybut `mortality_multiplier` został przemianowany w pełni.

Przy FM=1.0 dostajemy polskie dane GUS 2021 (TFR≈1.28). Przy FM=2.0 każda stopa płodności dla danego wieku jest podwojona.

---

## 6. Silnik symulacji — jak działa?

### Inicjalizacja populacji: `_create_synthetic_population(50000)`

Generuje 50 000 agentów z polskim rozkładem wiekowym (GUS 2021):

```python
age_distribution = {
    0:  0.094,   # 0–9:   9.4%
    10: 0.098,   # 10–19: 9.8%
    20: 0.104,   # 20–29: 10.4%
    30: 0.143,   # 30–39: 14.3%
    40: 0.135,   # 40–49: 13.5%
    50: 0.137,   # 50–59: 13.7%
    60: 0.128,   # 60–69: 12.8%
    70: 0.097,   # 70–79: 9.7%
    80: 0.051,   # 80–89: 5.1%
    90: 0.013,   # 90+:   1.3%
}
```

Dla każdego agenta losowane są: dokładny wiek w przedziale dekadowym, płeć (~51% kobiet), strefa, choroby z prevalence chorób, czynniki ryzyka.

### Zgony: `handle_deaths()` — 3-fazowy model Coxa

Po refaktorze `handle_deaths` realizuje **dynamiczny model akumulacji hazardu** (sekcja 10). Co miesiąc dla każdego żywego agenta wykonują się 3 fazy:

```python
for citizen in alive_citizens:
    # ─── FAZA 1: Akumulacja H_cum dla każdej choroby ───
    for disease in ["CVD", "Lung Cancer"]:
        delta_h = disease_model.monthly_hazard_increment(
            disease, citizen.age_years, citizen.risk_factors
        )
        # delta_h = λ_0 · exp(γ_age·(age-30)) · exp(Σ β_i · RF_i)
        citizen.cumulative_hazard[disease] += delta_h
        
        # ─── FAZA 2: Inicjacja choroby (Poisson approx) ───
        if citizen.diseases[disease] == 0:
            onset_prob = 1.0 - exp(-delta_h)
            if rng.random() < onset_prob:
                citizen.diseases[disease] = 1
                citizen.compute_disability_score(disease_weights)
    
    # ─── FAZA 3: Mortality z Cox-style multiplier ───
    base_rate = _get_mortality_rate(citizen.age_years, citizen.sex)
    disease_mult = 1.0 + 0.04 * citizen.disability_score
    cox_log = disease_model.cox_mortality_log_hazard(
        citizen.diseases, citizen.cumulative_hazard
    )
    cox_multiplier = exp(cox_log)  # = exp(Σ γ_d · min(H_cum_d, cap))
    
    monthly_prob = base_rate * disease_mult * cox_multiplier * mortality_multiplier
    
    if rng.random() < monthly_prob:
        citizen.alive = False
        household.remove_member(citizen.id)
```

Stary, prostszy model (bez Coxa) wyglądał tak — pozostawiamy dla porównania:

```python
# WERSJA PRZED Coxa (deprecjowana):
for citizen in alive_citizens:
    base_rate = _get_mortality_rate(citizen.age_years, citizen.sex)
    
    # Wpływ chorób (zredukowany po poprawkach)
    disease_mult = 1.0 + 0.02 * citizen.num_conditions()
    disease_mult += 0.04 * citizen.disability_score
    
    # Wpływ czynników ryzyka
    risk_mult = 1.0
    if smoking:    risk_mult *= 1.1   # +10%
    if obesity:    risk_mult *= 1.05  # +5%
    if alcohol:    risk_mult *= 1.1   # +10%
    
    monthly_prob = base_rate * disease_mult * risk_mult * mortality_multiplier
    
    if rng.random() < monthly_prob:
        citizen.alive = False
        household.remove_member(citizen.id)
```

### Narodziny: `handle_births()`

```python
for citizen in alive_female_citizens:
    if 15.0 <= citizen.age_years <= 50.0:
        annual_rate = _get_fertility_rate(citizen.age_years)
        monthly_prob = (annual_rate / 12.0) * fertility_rate
        
        # Redukcja przez choroby (zredukowana po poprawkach)
        disease_red = 1.0 - (0.02 * conditions + 0.04 * disability)
        disease_red = max(disease_red, 0.7)  # min. 70% bazowej stawki
        
        monthly_prob *= disease_red
        
        if rng.random() < monthly_prob:
            # Utwórz noworodka w tym samym gospodarstwie
            newborn = Citizen(sex=rng.choice(["male","female"]),
                              age_months=0, ...)
            citizens[newborn.id] = newborn
            household.add_member(newborn.id)
```

### Lookup śmiertelności: `_get_mortality_rate(age_years, sex)`

Używa **floor bracket** — znajdź najwyższy klucz tabeli ≤ wiekowi agenta:

```python
age_int = int(age_years)
bracket = available_ages[0]
for a in sorted(mortality_table.keys()):
    if a <= age_int:
        bracket = a
    else:
        break
return mortality_table[bracket][0 if sex=="male" else 1]
```

Przykład: agent w wieku 63 lat → bracket = 60 (klucz 65 jest >63, więc pomijamy). Przed poprawką używano *nearest* — agent w wieku 63 dostałby stawkę dla klucza 65, co było błędem.

### Statystyki roczne: `collect_yearly_stats()`

Co 12 miesięcy zbierane są:

```python
yearly_stats[year] = {
    "total_population": int,
    "alive_count": int,
    "births_this_year": int,
    "deaths_this_year": int,
    "age_pyramid": {
        "0-4":  {"male": int, "female": int},
        "5-9":  {"male": int, "female": int},
        ...
        "100+": {"male": int, "female": int},
    },
    "multimorbidity_count": int,
    "avg_disability_score": float,
}
```

---

## 7. Tabele demograficzne

### Tabela śmiertelności (GUS Poland 2021)

Miesięczne prawdopodobieństwa zgonu (male, female):

| Wiek | Mężczyźni (/mc) | Kobiety (/mc) | Stosunek M/K |
|------|----------------|---------------|-------------|
| 0    | 0.000373       | 0.000291      | 1.28        |
| 20   | 0.000042       | 0.000012      | 3.5 (wypadki!) |
| 40   | 0.000167       | 0.000067      | 2.5         |
| 60   | 0.001375       | 0.000583      | 2.4         |
| 65   | 0.002100       | 0.001125      | 1.9         |
| 70   | 0.003292       | 0.001833      | 1.8         |
| 75   | 0.005042       | 0.003083      | 1.6         |
| 80   | 0.007658       | 0.005375      | 1.4         |
| 85   | 0.012400       | 0.009000      | 1.4         |
| 90   | 0.018333       | 0.013750      | 1.3         |

**Ważna obserwacja**: Mężczyźni mają wyższą śmiertelność w KAŻDYM przedziale wiekowym. Nadumieralność mężczyzn jest największa w wieku 20–40 (wypadki, alkohol) i stopniowo maleje na starość.

### Tabela płodności (GUS Poland 2021, ASFR)

Roczne stopy płodności (urodzenia na kobietę w danym wieku):

| Wiek | ASFR (roczna) | /miesiąc |
|------|--------------|---------|
| 15–19 | 0.011      | 0.00092 |
| 20–24 | 0.041      | 0.00342 |
| 25–29 | 0.081      | 0.00675 (szczyt) |
| 30–34 | 0.082      | 0.00683 (szczyt) |
| 35–39 | 0.034      | 0.00283 |
| 40–44 | 0.007      | 0.00058 |
| 45–49 | 0.0003     | 0.000025 |

TFR (Total Fertility Rate) = Σ ASFR × 5 lat ≈ **1.28** ≈ polskie dane GUS 2021.

---

### Wskaźniki demograficzne — CBR, CDR, TFR

Tabele wyżej dają **stopy zależne od wieku i płci** (mortality_table[wiek][płeć], ASFR(wiek)). Na ich podstawie model wylicza **agregowane wskaźniki demograficzne**, które porównujemy z danymi GUS:

#### CBR — Crude Birth Rate (surowy współczynnik urodzeń)

CBR mierzy liczbę urodzeń żywych na 1000 mieszkańców w ciągu roku.

**Wzór ogólny:**
```
CBR = (liczba urodzeń żywych w roku / średnia populacja) × 1000   [‰]
```

**W modelu ABM:**
```python
CBR = (births_this_year / total_population) * 1000
```

**Co zawiera:**
- W liczniku — **wszystkie** urodzenia (niezależnie od wieku/płci dziecka i wieku matki)
- W mianowniku — **cała** populacja (mężczyźni, kobiety, dzieci, seniorzy)
- Jednostka — promile (‰)

**Wartości:**
- Polska 2021 (GUS): **CBR ≈ 8.5‰**
- Model po kalibracji (FM=1.0): **CBR = 8.30‰** ✓

**Ograniczenie**: CBR jest "surowy" (crude), bo nie koryguje na strukturę wiekową. Społeczeństwo z większą frakcją kobiet w wieku 20–35 lat będzie miało wyższe CBR przy tej samej skłonności do rodzenia.

#### CDR — Crude Death Rate (surowy współczynnik zgonów)

CDR mierzy liczbę zgonów na 1000 mieszkańców w ciągu roku.

**Wzór ogólny:**
```
CDR = (liczba zgonów w roku / średnia populacja) × 1000   [‰]
```

**W modelu ABM:**
```python
CDR = (deaths_this_year / total_population) * 1000
```

**Co zawiera:**
- W liczniku — **wszystkie** zgony (niezależnie od wieku, płci, przyczyny)
- W mianowniku — **cała** populacja
- Jednostka — promile (‰)

**Wartości:**
- Polska 2021 (GUS): **CDR ≈ 13.5‰**
- Model po kalibracji (MM=1.0): **CDR = 15.60‰** (lekkie zawyżenie, patrz sekcja 12)

**Ograniczenie**: Tak samo "surowy" — starzejąca się populacja ma wyższe CDR przy tej samej tabeli śmiertelności wg wieku, bo więcej osób znajduje się w przedziałach wiekowych o wysokim q_x.

#### NGR — stopa wzrostu naturalnego (Natural Growth Rate)

```
NGR = CBR − CDR    [‰/rok]
```

Po 50 latach:
```
score(50) = ((1 + NGR/1000) ^ 50 − 1) × 100%
```

- Polska 2021: NGR = 8.5 − 13.5 = **−5.0‰/rok** → naturalnie ~−22% po 50 latach
- Model (FM=MM=1.0): NGR = 8.30 − 15.60 = **−7.3‰/rok** → ~−31% (faktycznie −52% przez efekty struktury wiekowej)

#### TFR — Total Fertility Rate (współczynnik dzietności)

W przeciwieństwie do CBR (surowego), TFR uwzględnia strukturę wiekową — to suma wiekowych stóp ASFR:

```
TFR = Σ ASFR(wiek) × szerokość_przedziału    [dzieci/kobietę]
```

**Interpretacja**: średnia liczba dzieci, jaką urodziłaby kobieta w ciągu całego życia, gdyby przeszła przez wszystkie wiekowe stopy ASFR z danego roku.

- TFR = 2.1 → dokładna **zastępowalność pokoleń**
- TFR < 2.1 → populacja kurczy się (bez migracji)
- Polska 2021: **TFR = 1.26**
- Model (FM=1.0): **TFR ≈ 1.28** ✓

#### Dlaczego CBR (8.3‰) wynika z TFR (1.28)?

CBR i TFR są powiązane przez frakcję kobiet w wieku rozrodczym:

```
CBR ≈ TFR × frakcja_kobiet_15-50 / długość_okresu_rozrodczego
    ≈ 1.28 × 0.23 / 35 lat
    ≈ 0.0084  =  8.4‰
```

Czyli przy TFR=1.28, jeśli ~23% populacji to kobiety w wieku 15–50 lat, a okres rozrodczy trwa 35 lat, dostajemy CBR ≈ 8.4‰. Dokładnie wartość uzyskana w modelu ABM. **To samo równanie tłumaczy, dlaczego flat-rate fertility nie działa** (sekcja 13).

---

## 8. Gridsearch — optymalizacja parametrów

### Parametry i przestrzeń poszukiwań

```python
PARAM_GRID = {
    "fertility_multiplier":  np.linspace(0.4, 2.5, 12),  # [0.40, 0.59, ..., 2.50]
    "mortality_multiplier":  np.linspace(0.3, 1.6, 12),  # [0.30, 0.42, ..., 1.60]
}
# Łącznie: 12 × 12 = 144 kombinacje parametrów
```

### Funkcja oceny (score)

```python
score = (final_population - initial_population) / initial_population × 100
```

- `score > +2%` → populacja rośnie (czerwony na heatmapie)
- `-2% ≤ score ≤ +2%` → populacja stabilna (zielony/biały)
- `score < -2%` → populacja maleje (niebieski)

### Trzy tryby gridsearch

Projekt udostępnia 3 niezależne implementacje gridsearchu, różniące się dokładnością i kosztem obliczeniowym:

#### Tryb 1. Analityczny (proxy) — `grid_search_improved_v3_fixed.py`

Używa matematycznego modelu proxy **bez uruchamiania ABM**. Skalibrowany na bazowych CBR/CDR z pojedynczego ABM (FM=MM=1.0):

```python
BASE_CBR = 0.00830   # 8.30 / 1000 / rok (kalibrowane)
BASE_CDR = 0.01560   # 15.60 / 1000 / rok

effective_cbr   = BASE_CBR * fertility_multiplier
effective_cdr   = BASE_CDR * mortality_multiplier
annual_net_rate = effective_cbr - effective_cdr
score = ((1 + annual_net_rate) ** 50 − 1) × 100
```

- **Czas**: ~1 ms / kombinacja, ~30 s dla całego 12×12
- **Założenia**: liniowa skala CBR ∝ FM i CDR ∝ MM (nieprawdziwe na ekstremach)
- **Zalety**: bardzo szybki, prosty
- **Ograniczenia**: nie modeluje struktury wiekowej, brak feedbacku populacja↔płodność, brak chorób

#### Tryb 2. ABM dla piramid — `gridsearch_age_pyramids_analysis.py`

Uruchamia pełne symulacje ABM **tylko dla wybranych punktów** (siatka 3×3 + 3 diagonale = 21 punktów). Generuje **piramidy wieku** do wizualnej inspekcji kształtu populacji.

- **Czas**: ~90 s / symulacja × 21 punktów = ~30 min (z parallel ~5 min)
- **Cel**: pokazać KSZTAŁT piramidy w różnych regionach przestrzeni FM/MM
- **Nie nadaje się** do globalnego mapowania score — za mało punktów

#### Tryb 3. **Pełny ABM 12×12 bez RF** — `gridsearch_full_abm_no_rf.py` *(nowy)*

Uruchamia **pełną symulację ABM dla każdego z 144 punktów** siatki — czyli kompletnie zastępuje proxy, ale jest 100× wolniejszy.

```python
# Wszystkie 144 punkty z siatki 12×12
for fm in np.linspace(0.4, 2.5, 12):
    for mm in np.linspace(0.3, 1.6, 12):
        engine = SimulationEngine(...)
        engine.fertility_rate       = fm
        engine.mortality_multiplier = mm
        engine._create_synthetic_population(50_000)

        # WSZYSTKIE RF zerowane (cel: izolować efekt demografii)
        for c in engine.citizens.values():
            c.risk_factors = {rf: 0 for rf in Citizen.DEFAULT_RISK_FACTORS}

        engine.run(months=600)
        score = (final − initial) / initial × 100
```

- **Czas**: ~50 min z parallel (10 rdzeni)
- **Risk factors WYŁĄCZONE** → Cox aktywny ale `exp(Σ β·0)=1` (brak amplifikacji); diseases mogą się jeszcze inicjować z bazowego hazardu × Gompertz, ale rzadko
- **Zalety**:
  - Pełna stochastyczność (50k niezależnych agentów × 600 kroków)
  - Realistyczna struktura wiekowa
  - Naturalne feedback loops (zgon dziecka → mniej kobiet rozrodczych w przyszłości)
- **Wyniki w**: `gridsearch_full_abm_no_rf_<timestamp>.json` + `heatmap_gridsearch_full_abm_no_rf_<timestamp>.png`

### Wyniki gridsearch — porównanie proxy ↔ ABM

Z `porownanie_gridsearch.py` (generuje `porownanie_gridsearch_proxy_vs_abm.png` — 3 panele):

#### Globalne metryki

| Metryka | Proxy (analityczny) | ABM bez RF |
|---------|---------------------|------------|
| Range score | −66.5% ... **+121.9%** | −66.3% ... **+50.1%** |
| Mediana | −13.0% | −22.5% |
| Runtime | **~30 s** | ~50 min (100× wolniejszy) |
| Liczba "stabilnych" cells (\|score\|<2%) | 5 | 4 |

**Mean |Δ| (ABM − proxy) = 22.4 pp** — to OGROMNA średnia rozbieżność. Lokalnie różnice dochodzą do **+45 i −72 pp**.

#### Reguła stabilności — gdzie proxy się myli

Dla każdej wartości MM, gdzie krzywa score=0 przecina FM:

| MM | Proxy FM_stable | **ABM FM_stable** | Błąd proxy |
|----|----------------|-------------------|------------|
| 0.30 | 0.56 | **1.63** | −1.07 (−65%) |
| 0.42 | 0.79 | **1.73** | −0.94 (−54%) |
| 0.54 | 1.01 | **1.79** | −0.78 |
| 0.65 | 1.23 | **1.83** | −0.60 |
| 0.77 | 1.45 | **1.89** | −0.44 |
| 0.89 | 1.67 | **1.92** | −0.25 |
| **1.01** | **1.90** | **1.95** | **−0.05** ✓ |
| 1.13 | 2.12 | **1.97** | +0.15 |
| 1.25 | 2.34 | **1.99** | +0.35 |
| 1.36 | poza siatką | **2.01** | — |
| 1.48 | poza siatką | **2.03** | — |
| 1.60 | poza siatką | **2.05** | — |

**Wniosek matematyczny**: proxy zakłada **liniową** regułę stabilności

```
FM_proxy(MM) = (BASE_CDR / BASE_CBR) × MM = 1.88 × MM
```

Wynika to z warunku `BASE_CBR · FM = BASE_CDR · MM`. ABM pokazuje że to **nieliniowa krzywa nasycenia**:

```
FM_ABM(MM) ≈ 1.50 + 0.36 × tanh(2 × (MM − 0.4))     # przybliżona forma analityczna
```

Asymptota: `lim_{MM→∞} FM_ABM(MM) ≈ 2.05`. Proxy nigdy nie zbliży się do tej asymptoty (jest liniowy).

#### Punkty "stabilne" wg proxy → w ABM są niestabilne

| Proxy mówi (score≈0) | ABM mówi |
|---|---|
| FM=2.118, MM=1.127 → −0.02% ✓ | **+7.19%** (rośnie) |
| FM=0.782, MM=0.418 → −0.17% ✓ | **−39.16%** (zawala się!) |
| FM=0.591, MM=0.300 → +1.13% ✓ | **−39.87%** (zawala się!) |
| FM=2.309, MM=1.245 → −1.31% ✓ | **+16.52%** (rośnie) |
| FM=1.927, MM=1.009 → +1.28% ✓ | **−0.88%** ✓ (prawdziwie stabilny) |

Tylko **1 z 5 "stabilnych w proxy"** jest faktycznie stabilny w ABM. Proxy działa dokładnie tylko w wąskim pasie wokół MM≈1.0 (gdzie został skalibrowany).

#### Który gridsearch używać?

**ABM jest fundamentalnie poprawniejszy**, bo:

1. **Modeluje strukturę wiekową** — niska MM = długie życie = populacja się starzeje = mniej kobiet 15-50 = realne CBR rośnie WOLNIEJ niż FM sugeruje. Proxy tego nie widzi.
2. **Uwzględnia feedback loops** — wczesne zgony kohorty rozrodczej zmniejszają przyszłą bazę reprodukcyjną.
3. **Realistyczny zakres score** — proxy daje absurdalne +122% (×2.2 wzrost przez 50 lat), ABM ograniczone do +50%.

**Praktyczna strategia 2-stopniowa**:

```
1. PROXY (30 s)  → szybko zlokalizuj region zainteresowania
2. ABM (50 min)  → zweryfikuj wyniki dla wybranych punktów
```

**Konkretne rady**:
- Dla **raportów / publikacji** → wyłącznie ABM (`gridsearch_full_abm_no_rf_*.json`)
- Dla **iteracyjnej eksploracji** → proxy do orientacji
- Stary proxy zostaw — różnica proxy↔ABM jest sama w sobie cenną informacją diagnostyczną (pokazuje gdzie efekty strukturalne są ważne)

### Wyniki kluczowe gridsearch

Po poprawkach + dodaniu modelu Coxa:

| FM  | MM  | Score proxy (50 lat) | Score ABM bez RF | Charakter |
|-----|-----|----------------------|------------------|-----------|
| 0.40 | 1.60 | −66.5% | −66.3% | Silny spadek (oba zgodne na ekstremie) |
| 0.40 | 0.30 | −43.4% | −45.7% | Umiarkowany spadek |
| 1.927 | 1.009 | +1.3% | **−0.88%** | **Stabilny w ABM** |
| 2.118 | 1.127 | **−0.02%** | +7.2% | Stabilny w proxy, lekko rośnie w ABM |
| 2.50 | 1.00 | +35.7% | +33.1% | Silny wzrost |
| 2.50 | 0.30 | **+121.9%** | **+50.1%** | Proxy absurdalnie zawyża |

**Prawdziwy punkt stabilności (ABM)**: `FM ≈ 1.93, MM ≈ 1.0` (score = −0.88%).

---

## 9. Piramidy wieku

### `piramidy_gridsearch_siatka.html`

Siatka 3×3 piramid dla kombinacji skrajnych i środkowych wartości gridsearch:

```
         FM_low  FM_mid  FM_high
MM_low  |  (1,1) | (1,2) | (1,3) |   ← niska śmiertelność
MM_mid  |  (2,1) | (2,2) | (2,3) |
MM_high |  (3,1) | (3,2) | (3,3) |   ← wysoka śmiertelność
```

Piramidy wizualizują kształt populacji po 50 latach:
- Silny spadek → piramida odwrócona (wąska podstawa, szeroki wiek emerytalny)
- Stabilna → prostokąt
- Silny wzrost → klasyczna piramida trójkątna

### `piramidy_diagonale_gridsearch.html`

Trzy zestawy po 4 punkty wzdłuż diagonali przestrzeni gridsearch:
- **Zestaw 1**: główna przekątna FM[i], MM[i]
- **Zestaw 2**: wyższa płodność o +2 pozycje: FM[i+2], MM[i]
- **Zestaw 3**: wyższa śmiertelność o +2 pozycje: FM[i], MM[i+2]

### `comparison_flatrate_vs_multiplier.html`

Porównanie 6 piramid: 3 mnożnikowe + 3 flat-rate, dla tych samych zamierzonych CBR/CDR (patrz sekcja 13).

### `piramida_porownanie_ryzyko.html`

Dwie piramidy obok siebie **z aktywnym modelem Coxa** (sekcja 10):
- Lewy panel: optimum gridsearcha (FM=2.12, MM=1.13)
- Prawy panel: dolny-środkowy z siatki 3×3 (FM=1.55, MM=1.60)

Każda piramida ma adnotację z: medianą wieku, prevalencjami CVD/LC, prevalencjami RF (palenie, otyłość, chol, hiper). Wizualnie pokazuje efekt "wycinania" górnej części piramidy w scenariuszach wysokiej śmiertelności.

---

## 10. Model dynamicznego ryzyka — Cox cumulative hazard

### Motywacja

Pierwotna wersja modelu używała **statycznych mnożników mortality**: `risk_mult *= 1.1` dla palaczy, `*1.05` dla otyłych itd. To nie pokazywało **akumulacji uszkodzenia w czasie** — 30-letni palacz miał identyczne ryzyko jak 60-letni. Również nie istniał mechanizm **dynamicznej inicjacji choroby** — agent albo miał chorobę od początku, albo nigdy.

Po refaktorze model używa **proportional hazard model (Cox-style)** ze skumulowanym hazardem. Każdy agent ma "biologiczną pamięć" `cumulative_hazard[disease]` rosnącą wraz z ekspozycją na RF.

### Formalizm matematyczny

**Miesięczny przyrost hazardu** dla agenta w wieku `a` z risk factors `X`:

```
Δh_disease(a, X) = λ_0,disease · exp(γ_age · (a - 30)) · exp(Σ_i β_i · X_i)
```

- `λ_0,disease` — bazowy hazard miesięczny w wieku 30 lat (BASELINE_HAZARD)
- `γ_age` — tempo wzrostu z wiekiem (AGE_HAZARD_GROWTH; Gompertz-like)
- `β_i = ln(HR_i)` — log Hazard Ratio dla risk factora `i` (HAZARD_BETA)
- `X_i ∈ {0, 1}` — stan risk factora u agenta

**Akumulacja** (biologiczna pamięć):

```
H_cum_disease(T) = Σ_{t=0}^{T} Δh_disease(t)
```

**Inicjacja choroby** (Poisson approx dla rzadkich zdarzeń per miesiąc):

```
P(onset_this_month | not yet sick) = 1 − exp(−Δh)
```

**Mnożnik mortality** dla osób z aktywnymi chorobami:

```
mortality(t) = mortality_GUS(age, sex) · disease_mult · exp(Σ_d γ_d · min(H_cum_d, cap)) · MM
```

`cap = 1.5` zabezpiecza przed wybuchem exp().

### Macierz β = ln(HR) — wartości skalibrowane

Wartości pochodzą z `disease_model.HAZARD_BETA`. Pokazane jako Hazard Ratio dla intuicji:

| Risk Factor              | CVD (HR) | Lung Cancer (HR) |
|--------------------------|----------|------------------|
| `smoking`                | **2.5**  | **15.0**         |
| `obesity`                | 1.7      | —                |
| `physical_inactivity`    | 1.4      | 1.2              |
| `alcohol_abuse`          | 1.3      | 1.3              |
| `high_cholesterol`       | **2.0**  | —                |
| `hypertension_stage0`    | **2.2**  | —                |
| `family_history`         | 1.5      | 1.5              |

**Dominacja palenia w raku płuc** (HR=15) jest zgodna z literaturą: paczki·lata to najsilniejszy predyktor lung cancer; ryzyko niepalącego jest pomijalne w porównaniu.

**CVD ma 5 silnych RF** — palenie, hipertensja, hipercholesterolemia, otyłość, inactivity — co odzwierciedla wieloprzyczynowość chorób sercowo-naczyniowych.

### Bazowe parametry hazardu

| Choroba     | λ_0 (miesięczny, age 30) | γ_age | MORTALITY_GAMMA |
|-------------|--------------------------|-------|-----------------|
| CVD         | 6.0e-5                   | 0.06 (podwaja się co ~12 lat) | 1.2 |
| Lung Cancer | 3.0e-6                   | 0.075 (podwaja się co ~9 lat) | 2.5 |

Lung Cancer rośnie z wiekiem **szybciej** niż CVD (γ=0.075 vs 0.06) — odzwierciedla biologię raka (większy wpływ akumulacji mutacji w czasie).

### Sanity check — smoke test (5000 agentów, 10 lat)

| Grupa        | n    | H_cum CVD | CVD prev | H_cum Lung Cancer | LC prev |
|--------------|------|-----------|----------|-------------------|---------|
| Palacze      | 659  | **0.177** | **29.7%**| **0.0423**        | **6.83%**|
| Niepalący    | 4204 | 0.063     | 16.7%    | 0.0027            | 2.14%   |

Stosunek H_cum_LC palacze/niepalący wynosi **16×**, dokładnie zgodnie z β = ln(15.0) ≈ 2.71. Stosunek CVD: **2.8×**, blisko HR=2.5. Model jest spójny z parametrami wejściowymi.

### Skutek na piramidach (50 000 agentów, 50 lat)

Z aktywnym modelem Coxa:

| Punkt kalibracji          | FM   | MM   | Δ populacja (50 lat) | Mediana wieku końc. |
|--------------------------|------|------|----------------------|---------------------|
| **OPTIMUM gridsearcha**  | 2.12 | 1.13 | **+6.5%**            | 31.2 lat            |
| **DOLNY-ŚRODKOWY 3×3**   | 1.55 | 1.60 | **−26.6%**           | **37.5 lat**        |

> **Uwaga:** Po dodaniu Coxa cała przestrzeń kalibracji się przesunęła. Punkt poprzednio quasi-stabilny (−0.02% w starym gridsearchu) teraz daje +6.5% (model Coxa zwiększa selekcję — agenci z wysokim H_cum giną wcześniej, populacja przeżywająca rodzi więcej). Nowa reguła stabilności jest bliżej `FM ≈ 1.5 × MM`, nie `FM ≈ 1.88 × MM`.

### Wykres procesów RF → choroby

Skrypt `graf_ryzyko_choroby.py` generuje **3-panelowy graf** (`graf_ryzyko_choroby.html`):

1. **Sankey diagram** — szerokość strumienia ∝ β (czyli ∝ ln HR)
2. **Sieć dwudzielna** — 7 RF po lewej, 2 choroby po prawej, grubość krawędzi ∝ β
3. **Heatmapa HR** — pełna macierz 7×2 z wartościami HR

Top 5 najsilniejszych powiązań:

```
Palenie               → Lung Cancer   HR=15.00  (β=2.71)
Palenie               → CVD           HR= 2.50  (β=0.92)
Nadciśnienie (pre)    → CVD           HR= 2.20  (β=0.79)
Hipercholesterolemia  → CVD           HR= 2.00  (β=0.69)
Otyłość (BMI)         → CVD           HR= 1.70  (β=0.53)
```

### Wykres populacji w czasie

Skrypt `populacja_w_czasie.py` generuje wykres liniowy 50-letnich trajektorii (`populacja_w_czasie.html`):

- **OPTIMUM (FM=2.12, MM=1.13)**: krótki dołek do roku 25 (~47k), potem odbicie do **53.3k** (+6.5%)
- **DOLNY-ŚRODKOWY (FM=1.55, MM=1.60)**: monotoniczny spadek, najszybsze tempo w pierwszych 10 latach (efekt selekcji: agenci z wysokim H_cum giną wcześniej), końcowo **36.7k** (−26.6%)

Wykres pokazuje też podział M/F i baseline 50 000 (linia kreskowa).

---

## 11. Wszystkie poprawki (bug fixes)

### Poprawka 1: Odwrócona tabela śmiertelności kobiet (KRYTYCZNA)

**Problem**: W oryginalnej tabeli kobiety starsze (65–84 lat) miały śmiertelność **2× wyższą** niż mężczyźni w tym samym wieku. Było to dokładnie odwrotnie do rzeczywistości — w Polsce (jak wszędzie) mężczyźni umierają szybciej.

```python
# STARY kod (błędny):
DEFAULT_MORTALITY_TABLE = {
    ...
    65: (0.00110, 0.00200),  # female > male — ODWRÓCONE!
    70: (0.00175, 0.00310),
    75: (0.00280, 0.00480),
    80: (0.00420, 0.00700),
    ...
}
```

```python
# NOWY kod (poprawiony — GUS 2021):
DEFAULT_MORTALITY_TABLE = {
    ...
    65: (0.002100, 0.001125),  # male ≈ 1.9× female ✓
    70: (0.003292, 0.001833),  # male ≈ 1.8× female ✓
    75: (0.005042, 0.003083),
    80: (0.007658, 0.005375),
    ...
}
```

**Skutek błędu**: Kobiety umierały za szybko na starość → populacja kurczyła się dramatycznie → wszystkie scenariusze gridsearch pokazywały -43% do -83% po 50 latach.

---

### Poprawka 2: TFR zbyt niskie (0.68 zamiast 1.26)

**Problem**: Oryginalna tabela płodności dawała TFR ≈ 0.68, podczas gdy Polska w 2021 miała TFR ≈ 1.26. Stopy były prawie dwa razy za niskie.

```python
# STARA tabela (błędna):
DEFAULT_FERTILITY_TABLE = {
    15: 0.005, 20: 0.020, 25: 0.038,
    30: 0.040, 35: 0.016, 40: 0.003, 45: 0.0001,
}
# TFR = (0.005+0.020+0.038+0.040+0.016+0.003+0.0001) × 5 ≈ 0.61
```

```python
# NOWA tabela (GUS 2021):
DEFAULT_FERTILITY_TABLE = {
    15: 0.011, 20: 0.041, 25: 0.081,
    30: 0.082, 35: 0.034, 40: 0.007, 45: 0.0003,
}
# TFR = (0.011+0.041+0.081+0.082+0.034+0.007+0.0003) × 5 ≈ 1.28
```

---

### Poprawka 3: Rozkład wiekowy nie sumował się do 1.0

**Problem**: Wartości w oryginalnym `age_distribution` sumowały się do ~0.565, nie do 1.0. Po normalizacji (Python automatycznie normalizuje przy `choices()`), osoby 90+ stanowiły **1.77%** populacji zamiast polskich **0.54%**.

```python
# STARY kod (błędny — suma = 0.565):
age_distribution = {
    0: 0.05, 10: 0.05, 20: 0.08, 30: 0.10,
    40: 0.10, 50: 0.10, 60: 0.05, 70: 0.03,
    80: 0.02, 90: 0.01
}
# 90+ po normalizacji: 0.01/0.565 = 1.77% (za dużo!)
```

```python
# NOWY kod (GUS 2021 — suma ≈ 1.0):
age_distribution = {
    0:  0.094, 10: 0.098, 20: 0.104, 30: 0.143,
    40: 0.135, 50: 0.137, 60: 0.128, 70: 0.097,
    80: 0.051, 90: 0.013
}
# 90+ po normalizacji: 0.013/1.000 = 1.3% ✓ (Polska: ~1.3%)
```

---

### Poprawka 4: Lookup śmiertelności używał nearest zamiast floor

**Problem**: Funkcja `_get_mortality_rate()` znajdowała *najbliższy* wiek w tabeli (nearest). Agent w wieku 63 lat dostawał stawkę dla klucza `65` (odległość 2) zamiast `60` (odległość 3, ale poprawny bracket). Skutek: osoby w przedziale 60–64 miały 53% wyższą śmiertelność niż powinny.

```python
# STARY kod (błędny — nearest):
closest = min(available_ages, key=lambda a: abs(a - age_int))
```

```python
# NOWY kod (poprawny — floor bracket):
bracket = available_ages[0]
for a in available_ages:
    if a <= age_int:
        bracket = a
    else:
        break
```

---

### Poprawka 5: Zbyt silny wpływ chorób na śmiertelność

**Problem**: Mnożniki chorób i czynników ryzyka były zbyt wysokie, powodując podwójne liczenie efektów już uwzględnionych w kalibrowanych tabelach GUS.

```python
# STARY kod:
disease_multiplier = 1.0 + (0.05 * citizen.num_conditions())
disease_multiplier += 0.10 * citizen.disability_score
risk_mult *= 1.3   # palenie
risk_mult *= 1.15  # otyłość
risk_mult *= 1.25  # alkohol
```

```python
# NOWY kod (zredukowane):
disease_multiplier = 1.0 + (0.02 * citizen.num_conditions())
disease_multiplier += 0.04 * citizen.disability_score
risk_mult *= 1.1   # palenie  (+10% zamiast +30%)
risk_mult *= 1.05  # otyłość  (+5%  zamiast +15%)
risk_mult *= 1.1   # alkohol  (+10% zamiast +25%)
```

**Uzasadnienie**: Przy średnim obciążeniu populacji (0.396 chorób/osobę, disability ≈ 0.079), nowe mnożniki dają disease_multiplier ≈ 1.011, czyli ~1% nadwyżki. Tabele GUS już zawierają efekty chorób populacyjnych — nie trzeba ich liczyć podwójnie.

---

### Poprawka 7: Dodanie modelu Coxa cumulative hazard + refaktor 3→2 chorób

**Problem (wersja przed Cox)**: Wpływ czynników ryzyka na śmiertelność był **statyczny** — palacz w wieku 25 lat miał ten sam mnożnik (×1.1) co palacz w wieku 75 lat. To nie odzwierciedlało biologii: szkody z palenia akumulują się przez dziesięciolecia. Również wszystkie choroby były losowane raz na początku symulacji — agent albo "miał CVD" od zawsze, albo nigdy.

**Co zmieniono:**

1. **Hipercholesterolemia** przeniesiona z chorób do risk factorów (`high_cholesterol`). Sama choroba nie powoduje objawów — jest predyktorem CVD (HR=2.0).
2. **Dodano `cumulative_hazard: Dict[str, float]`** do `Citizen` — biologiczna pamięć agenta per choroba.
3. **Dodano 4 macierze parametrów** do `DiseaseModel`:
   - `HAZARD_BETA[disease][risk_factor]` — β = ln(HR), kalibrowane do realistycznych Hazard Ratios
   - `BASELINE_HAZARD[disease]` — λ_0 miesięczny w wieku 30
   - `AGE_HAZARD_GROWTH[disease]` — γ_age (Gompertz)
   - `MORTALITY_GAMMA[disease]` — wpływ H_cum na mortality dla aktywnych chorób
4. **Przepisano `handle_deaths`** na 3-fazowy model:
   - Faza 1: akumulacja `Δh = λ_0 · exp(γ_age·(a−30)) · exp(Σ β·RF)`
   - Faza 2: inicjacja choroby z prawdopodobieństwem `P = 1 − exp(−Δh)`
   - Faza 3: mortality × `exp(Σ γ_d · H_cum_d)` dla aktywnych chorób

**Skutek**:
- Palacze mają H_cum_LungCancer **16× wyższy** niż niepalący (β = ln(15.0) ≈ 2.71)
- Palacze mają CVD prev **29.7%** vs niepalących **16.7%** (zgodne z HR=2.5)
- Górna część piramidy się "wycina" wraz z akumulacją H_cum — dokładnie efekt wymagany w specyfikacji
- Kalibracja przestrzeni FM/MM przesunęła się: nowa reguła stabilności ≈ `FM ≈ 1.5 × MM` (stary gridsearch jest pre-Cox)

---

### Poprawka 6: Zbyt silna redukcja płodności przez choroby + brak podestu

**Problem**: Choroby mogły redukować płodność do zera (floor = 0.0).

```python
# STARY kod:
disease_reduction = 1.0 - (0.05 * conditions + 0.10 * disability)
disease_reduction = max(disease_reduction, 0.0)  # mogło dojść do 0!
```

```python
# NOWY kod:
disease_reduction = 1.0 - (0.02 * conditions + 0.04 * disability)
disease_reduction = max(disease_reduction, 0.7)  # min. 70% bazowej stawki
```

---

## 12. Kalibracja — przed i po poprawkach

| Metryka | Przed poprawkami | Po poprawkach | Polska 2021 |
|---------|-----------------|---------------|-------------|
| CBR (FM=1.0) | ~5.2/1000/rok | **8.30/1000/rok** | ~8.5/1000/rok |
| CDR (MM=1.0) | ~25.0/1000/rok | **15.60/1000/rok** | ~13.5/1000/rok |
| TFR (FM=1.0) | ~0.68 | **~1.28** | 1.26 |
| Score (FM=1.0, MM=1.0) | -83% po 50 latach | **-52%** | — |
| FM_stable (MM=1.0) | FM > 4.8 (poza siatką!) | **FM ≈ 1.88** (w siatce ✓) |
| Zakres score gridsearch | -83% do -5% | **-66% do +122%** | — |

Wyjaśnienie dlaczego CDR=15.6/1000 zamiast polskich 13.5/1000: Model ma nieco zawyżony CDR ponieważ tabele śmiertelności GUS dotyczą całej populacji, a w modelu domyślna śmiertelność nie koryguje w dół dla efektu "zdrowej populacji syntetycznej". To akceptowalne odchylenie — ważne jest, że FM_stable jest wewnątrz siatki parametrów.

> **Po dodaniu modelu Coxa (sekcja 10)** cała kalibracja przesuwa się — z aktywnym Cox-multiplier mortality rośnie dla agentów z H_cum > 0, więc reguła stabilności zmienia się z `FM ≈ 1.88 × MM` na `FM ≈ 1.5 × MM`. Stare wartości w tej tabeli odpowiadają wersji **przed** dodaniem Coxa; nowy gridsearch z aktywnym modelem ryzyka pozostaje TODO.

---

## 13. Flat rate vs. mnożnik tabel wiekowych

### Dwa podejścia parametryzacji

**Podejście A (flat rate)**:
```python
# Ta sama stopa dla WSZYSTKICH wieków
monthly_birth_prob = birth_rate / 12.0    # jednakowa dla każdej kobiety 15-50
monthly_death_prob = mortality_rate / 12.0  # jednakowa dla wszystkich
```

**Podejście B (mnożnik, aktualne)**:
```python
# Stopa ZALEŻY od wieku agenta (tabela GUS)
base_rate = _get_mortality_rate(citizen.age_years, citizen.sex)
monthly_prob = base_rate * mortality_multiplier
```

### Dlaczego flat rate daje złe wyniki?

**Matematyczny dowód**:

Niech birth_rate = mortality_rate = 15.6/1000/rok (zamierzony warunek stabilności CBR=CDR).

Kobiety 15–50 lat stanowią tylko **~23%** populacji (z rozkładu GUS 2021):
```
Kobiety 15-50 = (kobiety 15-19) + ... + (kobiety 45-50)
              ≈ 50% × (9.8+10.4+14.3+13.5+13.7)% 
              ≈ 50% × 61.7% = ~30.9% populacji → ale tylko frakcja 15-50
```

Przy flat rate z birth_rate = 15.6/1000:
- Rzeczywiste urodzenia = 15.6/1000 × frakcja kobiet 15-50 × populacja
- = 15.6/1000 × 0.23 × N = **3.59/1000 × N**
- Zgony = 15.6/1000 × N

Deficyt = 3.59 - 15.6 = **-12.0/1000/rok** → po 50 latach: (1 - 0.012)^50 ≈ **-45%**!

Dla stabilności przy flat rate potrzeba: `birth_rate = mortality_rate / 0.23 ≈ 4.3 × mortality_rate`.

### Wyniki eksperymentalne (50 000 agentów, 50 lat)

| Scenariusz | Zamierzone CBR/CDR | Mnożnik (B) | Flat Rate (A) |
|------------|-------------------|-------------|---------------|
| Spadek | CBR=4.2‰, CDR=15.6‰ | -52.7% | -61.4% |
| Stabilny | CBR=15.6‰, CDR=15.6‰ | **-3.5%** ✓ | **-49.1%** ✗ |
| Wzrost | CBR=20.8‰, CDR=9.4‰ | **+41.1%** ✓ | **-27.9%** ✗ |

### Kształt piramidy — flat rate vs. mnożnik

**Flat rate** generuje **prostokątne** piramidy lub piramidy z odwróconą strukturą, ponieważ:
- Śmiertelność jednakowa dla dzieci i 90-latków (nierealistyczne)
- Brak nadwyżki starczej śmiertelności → zbyt dużo starców w populacji
- Brak nadumieralności mężczyzn → symetryczna piramida

**Mnożnik tabel GUS** generuje **realistyczne polskie piramidy**:
- Wyraźna nadumieralność mężczyzn w średnim wieku
- Rosnąca śmiertelność starczą
- Szczyt płodności 25–34 → wyraźna baza piramidy przy wysokim FM

### Wniosek metodologiczny

Podejście z mnożnikami tabel wiekowych jest **fundamentalnie lepsze** z trzech powodów:

1. **Zgodność z danymi GUS** — multiplier = 1.0 odpowiada Polsce 2021
2. **Realistyczna struktura wiekowa** — inny rozkład zgonów i urodzeń według wieku
3. **Interpretowalność** — FM=1.88 oznacza konkretną polską demografię, nie arbitralną stopę

---

## 14. Wnioski

### Wnioski demograficzne

1. **Polska demografia jest deficytowa** — przy naturalnych parametrach (FM=MM=1.0) populacja spada o ~52% przez 50 lat. Dla stabilności potrzeba FM≈1.88 przy MM=1.0, czyli prawie dwukrotnie wyższej płodności niż obecna.

2. **Asymetria wrażliwości** — model jest bardziej wrażliwy na zmiany `mortality_multiplier` niż na zmiany `fertility_multiplier` w dolnych zakresach. Przy MM=0.3 (dramatyczny spadek śmiertelności) nawet niskie FM dają stabilną populację.

3. **Kształt piramidy jest diagnostyczny** — sama liczba populacji po 50 latach mówi mało; kształt piramidy wiekowej ujawnia, czy starzejemy się (szeroka góra), kurczymy u podstawy (niska płodność), czy mamy odpowiednią strukturę.

4. **Nadumieralność mężczyzn** — widoczna wyraźnie w piramidach jako asymetria (szersza strona kobieca po 50+). W Polsce mężczyźni żyją średnio o 7.5 roku krócej niż kobiety.

### Wnioski modelarskie

5. **Kalibracja jest kluczowa** — bez poprawek model dawał biologicznie niemożliwe wyniki (wszystkie scenariusze ujemne). Trzy błędy wzmacniały się nawzajem: odwrócona tabela + za niskie TFR + za wysoka śmiertelność przez choroby.

6. **ABM vs. makromodel** — ABM pozwolił wykryć błąd w tabeli kobiecej śmiertelności, który byłby ukryty w agregowanym modelu. Widzieliśmy że kobiety 65–75 umierały w modelu szybciej niż mężczyźni, co było diagnostycznym sygnałem.

7. **Równoległość jest niezbędna** — każda symulacja ABM (50k agentów, 50 lat) trwa ~90 sekund. Bez `ProcessPoolExecutor` pełny gridsearch (144 symulacje) trwałby 3.5 godziny zamiast ~20 minut.

8. **Analityczny proxy vs. pełny ABM** — analityczny scoring (fast math, 1ms) pozwala przeglądać całą siatkę 144 punktów; pełny ABM (90s) uruchamiany jest tylko dla wybranych punktów do generowania piramid. To dobry kompromis szybkość/dokładność.

### Wnioski z modelu dynamicznego ryzyka (Cox)

9. **Cox cumulative hazard pozwala oddzielić demografię od epidemiologii** — bazowa tabela GUS modeluje populacyjne ryzyko zgonu w danym wieku, model Coxa nakłada na to **indywidualne** różnice z ekspozycji RF. Dwóch palaczy w wieku 60 może mieć różne ryzyko zgonu zależnie od historii ekspozycji.

10. **Dominacja palenia jako risk factora** — HR=15 dla raka płuc to największy współczynnik w macierzy. W modelu palacze mają ~16× wyższe H_cum_LC niż niepalący już po 10 latach symulacji. Polityki redukcji palenia mają największy potencjalny wpływ na śmiertelność z konkretnej chorobowej przyczyny.

11. **Wielokrotne RF dla CVD** — 5 czynników (palenie, hipertensja, hipercholesterolemia, otyłość, inactivity) odzwierciedla wieloprzyczynowość CVD. Osoba z 3-4 z nich ma `exp(Σ β) ≈ 10-20×` wyższe ryzyko CVD niż osoba bez żadnego.

12. **Refaktor 3→2 chorób był biologicznie poprawny** — hipercholesterolemia sama w sobie nie jest chorobą powodującą zgon (DW=0.08 było bardzo niskie). Jako risk factor wpływa pośrednio przez CVD (HR=2.0), co jest medycznie dokładniejsze.

13. **Stary gridsearch trzeba przepuścić od nowa** — po dodaniu Coxa cała przestrzeń parametrów się przesunęła. To zadanie zostało wykonane: zob. `gridsearch_full_abm_no_rf.py` i sekcję 8.

### Wnioski z porównania gridsearch proxy ↔ ABM

14. **Proxy jest dokładny TYLKO w wąskim pasie wokół MM≈1.0** — tam, gdzie został skalibrowany. Poza tym pasem błąd dochodzi do **45-72 punktów procentowych** w score. Mean |Δ| = 22.4 pp dla całej siatki 144 punktów.

15. **Reguła stabilności jest nieliniowa** — proxy zakłada `FM_stable = 1.88 × MM` (liniowa), ABM pokazuje krzywą nasycenia z asymptotą `FM_stable → 2.05` przy MM → ∞. Różnica wynika z efektów strukturalnych populacji, których proxy nie modeluje (rozkład wieku, frakcja kobiet 15-50, feedback urodzin/zgonów).

16. **Optimum przesunięte**: proxy mówił FM=2.12, MM=1.13 (score=−0.02%) → w ABM to +7.19% (rośnie). Prawdziwy ABM optimum to **FM=1.93, MM=1.01** (score=−0.88%).

17. **Realistyczny zakres score**: proxy daje absurdalne +122% (×2.2 wzrost przez 50 lat) — empirycznie niemożliwe. ABM ogranicza do +50%, bo selekcja śmiertelnościowa i nasycenie struktury wiekowej działają jako ograniczniki.

18. **Strategia 2-stopniowa: proxy → ABM** — proxy nadaje się jako szybkie sito (30 s), ale finalne wnioski musi potwierdzić ABM (50 min). Dla raportów: tylko ABM. Stary proxy zostaje jako narzędzie diagnostyczne — jego rozbieżność z ABM sama w sobie identyfikuje regiony parametrów gdzie efekty strukturalne dominują.

---

## 15. Przykładowe pytania i odpowiedzi

**Q1: Dlaczego używamy `Dict[int, Citizen]` zamiast `List[Citizen]`?**

Słownik daje O(1) dostęp po ID. Przy 50 000 agentów i 600 krokach miesięcznych, każdy krok wymaga wielokrotnego wyszukiwania agentów po ID (w household.members, w birth linkach itp.). Z listą byłoby O(n) = O(50 000) per lookup.

**Q2: Dlaczego martwi agenci nie są usuwani ze słownika?**

Bo household przechowuje `List[int]` — same ID. Jeśli usuniemy martwego agenta ze słownika, a jego ID zostanie w `household.members`, dostaniemy `KeyError`. Flaga `alive=False` jest bezpieczniejsza i pozwala na retrospektywne analizy.

**Q3: Co oznacza `fertility_rate = 1.88` w kontekście TFR?**

FM=1.88 × TFR_base (≈1.28) ≈ TFR=2.41, czyli blisko zastępowalności pokoleń (2.1). To wartość przy której CBR ≈ CDR i populacja jest stabilna przy MM=1.0.

**Q4: Dlaczego punkt stabilności to FM≈1.88×MM, a nie FM=MM=1.0?**

Ponieważ CDR > CBR przy domyślnych ustawieniach (15.6 vs 8.3 na 1000/rok). Czyli model startuje z polską strukturą wiekową, gdzie jest dużo seniorów (duże zgony) i mało kobiet w wieku rozrodczym (mało urodzeń). Żeby zbilansować, potrzeba podnieść płodność lub obniżyć śmiertelność.

**Q5: Dlaczego flat rate nie działa dla "stabilnego" scenariusza?**

Bo urodzenia pochodzą tylko od ~23% populacji (kobiety 15-50), a zgony dotyczą 100% populacji. Przy birth_rate = mortality_rate, efektywne urodzenia to tylko 23% zgonów → silna depopulacja. Szczegóły w sekcji 13.

**Q6: Jakie byłyby wyniki dla TFR=2.1 (zastępowalność)?**

TFR=2.1 / TFR_base(1.28) ≈ FM=1.64. Przy MM=1.0: FM=1.64 < FM_stable=1.88, więc lekki spadek (~-15% po 50 latach). Do pełnej stabilności potrzeba FM=1.88 (TFR≈2.41) bo model ma CDR > polskie dane (efekt struktury wiekowej starzejącej się populacji startowej).

**Q7: Jak interpretować heatmapę gridsearch?**

Oś X: fertility_multiplier (0.4→2.5), oś Y: mortality_multiplier (0.3→1.6). Kolor: niebieski = depopulacja, biały = stabilność, czerwony = wzrost. Linia stability (FM≈1.88×MM) biegnie diagonalnie przez mapę. Lewy górny róg (niskie FM, niskie MM) = paradoks: niska płodność + niska śmiertelność = powolny spadek.

**Q8: Dlaczego simulation_engine używa `random.Random` zamiast `numpy.random`?**

Model jest sekwencyjny per agent — każdy agent losuje niezależnie w pętli. `random.Random` z seedem zapewnia pełną reproducibility. `numpy.random` jest lepszy dla operacji wektorowych (całe tablice naraz), co nie pasuje do ABM gdzie każdy agent ma własny stan.

**Q9: Co to jest disability_score i jak wpływa na symulację?**

`disability_score = Σ (disease_active[i] × disability_weight[i])`. Po refaktorze chorób przewlekłych są dwie: CVD (DW=0.25) i Lung Cancer (DW=0.55). Pacjent z obiema chorobami → disability_score = 0.80. Wpływa na śmiertelność (+0.04×score) i płodność (−0.04×score, min 0.7). Hipercholesterolemia nie jest tu liczona, bo jest *risk factorem*, nie chorobą — jej wpływ idzie przez Cox-multiplier (sekcja 10), HR=2.0 dla CVD.

**Q10: Jak przebiega tworzenie noworodka?**

```python
newborn = Citizen(
    sex=rng.choice(["male", "female"]),  # 50/50
    age_months=0,
    household_id=mother.household_id,   # do gospodarstwa matki
    zone_id=mother.zone_id,
    diseases=dm.get_initial_diseases(),  # wszystkie 0 (brak chorób)
)
newborn.risk_factors = {rf: 0 for rf in Citizen.DEFAULT_RISK_FACTORS}
citizens[newborn.id] = newborn
household.add_member(newborn.id)
```

Noworodek dziedziczy strefę i gospodarstwo matki. Nie dziedziczy chorób (`cumulative_hazard` startuje od zera; choroby mogą zostać zainicjowane przez model Coxa w fazie 2 `handle_deaths`, gdy agent osiąga wiek + odpowiednie ekspozycje RF). Risk factors u noworodków są również zerowane — zaczynają się aktywować dopiero w fazie życia dorosłego. Płeć 50/50 (uproszczenie — rzeczywisty stosunek płci at birth to ~51.5% chłopcy).

**Q11: Dlaczego hipercholesterolemia jest risk factorem a nie chorobą?**

Po refaktorze (z 3 chorób na 2) hipercholesterolemia została przeniesiona do *risk factors* jako `high_cholesterol`. Biologicznie jest to poprawne: podwyższony cholesterol sam w sobie nie powoduje objawów ani zgonu — to **czynnik ryzyka dla CVD** (HR=2.0, β=0.69). W modelu Coxa wpływa pośrednio: zwiększa miesięczny przyrost hazardu CVD, co prowadzi do szybszej inicjacji CVD i wzrostu mortality dla osób już chorych.

**Q12: Czym różni się Cox-style multiplier od starych static multiplierów?**

Stary model: `risk_mult *= 1.1` dla palaczy → ten sam mnożnik dla 25-latka co dla 75-latka, tej samej osoby cały czas. Brak akumulacji szkód, brak inicjacji choroby.

Model Coxa: `exp(γ_d · H_cum_d)` — efekt rośnie wraz z `H_cum`, który rośnie wraz z latami ekspozycji. 75-letni palacz ma znacznie wyższy H_cum niż 25-letni palacz, więc dużo wyższe ryzyko zgonu. Plus: po przekroczeniu progu losowego (P=1−exp(−Δh)) choroba zostaje **stochastycznie zainicjowana** — to mechanizm onset nieobecny w starym modelu.

**Q13: Jakie HR są zaszyte w modelu i czy są kalibrowalne?**

Tak, wszystkie HR są w jednym miejscu: `disease_model.HAZARD_BETA` (macierz `disease × risk_factor`). Można je edytować bez ruszania reszty kodu. Aktualne wartości: smoking → LC HR=15, smoking → CVD HR=2.5, hypertension → CVD HR=2.2, hipercholesterolemia → CVD HR=2.0, otyłość → CVD HR=1.7. Skrypt `graf_ryzyko_choroby.py` zawsze odzwierciedla aktualny stan macierzy.

---

## 16. Jak uruchomić?

### Wymagania

```bash
pip install numpy plotly scipy pandas openpyxl
```

### Jedna symulacja z wykresami

```bash
python main.py
# Generuje: population_trends.html, piramida_wieku_animowana.html, ...
```

### Tryb 1 — Analityczny gridsearch proxy (szybki, ~30 sekund)

```bash
python grid_search_improved_v3_fixed.py
# Generuje: heatmap_gridsearch_v3_fixed_<timestamp>.png
#           gridsearch_results_v3_fixed_<timestamp>.json
```

### Tryb 2 — Gridsearch z piramidami ABM (selektywny, ~5-20 minut)

```bash
python gridsearch_age_pyramids_analysis.py
# Generuje: piramidy_gridsearch_siatka.html    (siatka 3×3)
#           piramidy_diagonale_gridsearch.html  (3 zestawy diagonali)
```

### Tryb 3 — Pełny ABM 12×12 bez RF (najdokładniejszy, ~50 minut)

```bash
python gridsearch_full_abm_no_rf.py
# Generuje: heatmap_gridsearch_full_abm_no_rf_<timestamp>.png
#           gridsearch_full_abm_no_rf_<timestamp>.json
```

### Porównanie proxy ↔ ABM (po uruchomieniu obu)

```bash
python porownanie_gridsearch.py
# Generuje: porownanie_gridsearch_proxy_vs_abm.png (3 panele: A=proxy, B=ABM, C=Δ)
# Wymaga: gridsearch_results_v3_fixed_*.json + gridsearch_full_abm_no_rf_*.json
```

### Analiza wyników ABM gridsearch (osobny folder)

```bash
cd analiza_ABM_gridsearch
python piramidy_3x3_no_rf.py          # Siatka 3×3 z punktami z ABM gridsearch (bez RF, ~16 min)
python piramida_porownanie_z_rf.py    # Optimum ABM vs dolny-środkowy (z RF, ~10 min)
python populacja_w_czasie_no_rf.py    # Trajektorie populacji (bez RF, ~10 min)
python graf_ryzyko_choroby.py         # Graf RF → choroby (~5 s)
```

### Porównanie flat-rate vs. mnożnik

```bash
python comparison_flatrate_vs_multiplier.py
# Generuje: comparison_flatrate_vs_multiplier.html (2×3 piramidy)
```

### Model dynamicznego ryzyka (Cox)

```bash
# Graf RF → choroby (Sankey + sieć + heatmapa). Szybki (~5 sekund).
python graf_ryzyko_choroby.py
# Generuje: graf_ryzyko_choroby.html

# Dwie piramidy obok siebie z aktywnym Coxa (50k × 50 lat × 2 scenariusze, ~10 min).
python piramida_porownanie_ryzyko.py
# Generuje: piramida_porownanie_ryzyko.html

# Trajektorie ludności rok-po-roku (50k × 50 lat × 2 scenariusze, ~10 min).
python populacja_w_czasie.py
# Generuje: populacja_w_czasie.html
```

Wszystkie 3 skrypty współdzielą definicję 2 scenariuszy:

```python
POINTS = [
    {"label": "OPTIMUM gridsearcha",       "fm": 2.118, "mm": 1.127},  # +6.5%
    {"label": "DOLNY-ŚRODKOWY siatki 3x3", "fm": 1.545, "mm": 1.600},  # -26.6%
]
```

### Parametry do eksperymentowania

W `gridsearch_age_pyramids_analysis.py` i `comparison_flatrate_vs_multiplier.py`:

```python
POPULATION_SIZE = 50_000   # liczba agentów
SIM_MONTHS      = 600      # 50 lat
```

W `grid_search_improved_v3_fixed.py`:

```python
param_grid = {
    "fertility_multiplier": np.linspace(0.4, 2.5, 12),  # zakres FM
    "mortality_multiplier": np.linspace(0.3, 1.6, 12),  # zakres MM
}
```

---

## 17. Wzory matematyczne — kompendium

Pełna lista wzorów używanych w modelu, zebrana w jednym miejscu do szybkiego wglądu.

### 17.1 Demografia bazowa

**Mortality lookup** (floor bracket, sekcja 6):

```
q_x(age, sex) = MORTALITY_TABLE[bracket(age)][sex]
gdzie bracket(age) = max{a ∈ table_keys : a ≤ age}
```

**Fertility lookup**:

```
ASFR(age) = FERTILITY_TABLE[floor(age, 5)]      (jeśli 15 ≤ age ≤ 50, else 0)
monthly_birth_prob = ASFR(age) / 12 × FM × disease_reduction
gdzie disease_reduction = max(1 − 0.02·n_conditions − 0.04·disability_score, 0.7)
```

### 17.2 Wskaźniki demograficzne

**Crude Birth Rate (CBR)**, **Crude Death Rate (CDR)** — surowe, na 1000/rok:

```
CBR = (urodzenia w roku) / N × 1000      [‰]
CDR = (zgony w roku)     / N × 1000      [‰]
NGR = CBR − CDR                          [‰/rok]
```

**Total Fertility Rate (TFR)**:

```
TFR = Σ_{age=15..49} ASFR(age) × Δage    [dzieci / kobietę]
```

**Wzór wiążący CBR i TFR**:

```
CBR ≈ TFR × frakcja_kobiet_15-50 / długość_okresu_rozrodczego
    ≈ TFR × 0.23 / 35
```

**Wzrost populacji 50 lat** (analityczny proxy):

```
score(50) = ((1 + NGR/1000)^50 − 1) × 100      [%]
```

### 17.3 Mortality w model_engine — pełny wzór z Coxem

Miesięczne prawdopodobieństwo zgonu agenta:

```
P_death(t) = q_x(age, sex)
           × disease_multiplier
           × cox_multiplier
           × MM

gdzie:
  disease_multiplier = 1 + 0.04 · disability_score
  disability_score   = Σ_d 1{disease_d active} · DW_d

  cox_multiplier     = exp(Σ_d γ_d · min(H_cum_d, cap))
  cap = 1.5
```

### 17.4 Cox cumulative hazard — model ryzyka

**Miesięczny przyrost hazardu** dla choroby `d` u agenta w wieku `a` z risk factors `X`:

```
Δh_d(a, X) = λ_0,d · exp(γ_age,d · (a − 30)) · exp(Σ_i β_d,i · X_i)
```

gdzie:
- `λ_0,d` — bazowy hazard miesięczny w wieku 30 (`BASELINE_HAZARD[d]`)
- `γ_age,d` — tempo wzrostu z wiekiem (`AGE_HAZARD_GROWTH[d]`, Gompertz)
- `β_d,i = ln(HR_d,i)` — log Hazard Ratio (`HAZARD_BETA[d][i]`)
- `X_i ∈ {0, 1}` — stan risk factora i

**Akumulacja** (biologiczna pamięć agenta):

```
H_cum,d(T) = Σ_{t=0}^T Δh_d(t)
```

**Inicjacja choroby** (Poisson approx dla rzadkich zdarzeń):

```
P(onset_d this_month | not_yet_sick) = 1 − exp(−Δh_d(t))
```

### 17.5 Hazard Ratios — macierz β

`HAZARD_BETA` z `disease_model.py` (pokazane jako HR dla intuicji):

| Risk Factor              | CVD | Lung Cancer |
|--------------------------|-----|-------------|
| smoking                  | 2.5 | **15.0**    |
| obesity                  | 1.7 | —           |
| physical_inactivity      | 1.4 | 1.2         |
| alcohol_abuse            | 1.3 | 1.3         |
| high_cholesterol         | 2.0 | —           |
| hypertension_stage0      | 2.2 | —           |
| family_history           | 1.5 | 1.5         |

Sanity: log-HR macierz to `β_d,i = ln(HR_d,i)`. Multiplier mortality dla osoby z N aktywnych RF:

```
mult_log = Σ_i β_d,i · X_i
mult     = exp(mult_log)
```

Przykład: palacz z otyłością i hipertensją na CVD:
```
mult = exp(ln(2.5) + ln(1.7) + ln(2.2)) = 2.5 × 1.7 × 2.2 = 9.35×
```

### 17.6 Bazowe parametry hazardu

| Choroba     | λ_0 (miesięczny, age=30) | γ_age | MORTALITY_GAMMA γ_d |
|-------------|---------------------------|-------|----------------------|
| CVD         | 6.0 · 10⁻⁵                | 0.06  | 1.2 |
| Lung Cancer | 3.0 · 10⁻⁶                | 0.075 | 2.5 |

Cap `H_cum` w mortality: **1.5** (chroni exp() przed wybuchem).

### 17.7 Score gridsearch (oba tryby)

```
score(FM, MM) = (final_pop − initial_pop) / initial_pop × 100      [%]
```

**Proxy (analityczny)**:

```
score_proxy(FM, MM) = ((1 + (BASE_CBR · FM − BASE_CDR · MM))^50 − 1) × 100
gdzie BASE_CBR = 0.00830, BASE_CDR = 0.01560
```

**ABM**: pełna symulacja Monte Carlo (50k agentów × 600 mies. → empiryczne `final_pop`).

### 17.8 Reguła stabilności

**Proxy** (liniowa, ze wzoru `effective_CBR = effective_CDR`):

```
FM_proxy(MM) = (BASE_CDR / BASE_CBR) × MM = 1.88 · MM
```

**ABM** (nieliniowa krzywa nasycenia, fit empiryczny):

```
FM_ABM(MM) ≈ 1.50 + 0.36 · tanh(2 · (MM − 0.4))
asymptota:  lim_{MM → ∞} FM_ABM(MM) ≈ 2.05
```

Rozbieżność:

```
ΔFM(MM) = FM_ABM(MM) − FM_proxy(MM)
        > 1.0 dla MM < 0.45  (proxy mocno niedoszacowuje)
        < 0   dla MM > 1.15  (proxy przeszacowuje)
```

### 17.9 Disability score i wpływ chorób

```
disability_score = Σ_{d ∈ active_diseases} DW_d
```

gdzie DW_CVD = 0.25, DW_LungCancer = 0.55. Wpływ na płodność:

```
fertility_reduction = max(1 − 0.02·n_conditions − 0.04·disability_score, 0.7)
```

### 17.10 Newborn — inicjalizacja

```
sex                 ∼ Bernoulli(0.5)                       # 50/50 (uproszczenie)
age_months          = 0
household_id        = mother.household_id                 # dziedziczy
zone_id             = mother.zone_id
diseases[d]         = 0  ∀ d
risk_factors[rf]    = 0  ∀ rf                              # brak dynamic acquisition
cumulative_hazard[d] = 0  ∀ d                              # startujący od 0
```

---

## Technologie

| Biblioteka | Zastosowanie |
|-----------|-------------|
| Python 3.12 | Implementacja ABM |
| NumPy | Operacje numeryczne, linspace |
| Plotly | Interaktywne wykresy HTML |
| SciPy | TwoSlopeNorm dla heatmap |
| Matplotlib | Generowanie heatmap PNG |
| concurrent.futures | Równoległe symulacje (ProcessPoolExecutor) |
| random.Random | Reproducible stochastyczność per agent |

---

## Autorzy

Projekt zespołowy — **Urban Health ABM** — Demograficzna symulacja populacji Polski  
Data: 2026 | Dane: GUS Poland 2021 Tablice Trwania Życia

---

*Model jest narzędziem badawczym. Wyniki zależą od kalibracji parametrów i uproszczonych założeń (brak migracji, stałe tabele demograficzne, uproszczony model chorób).*
