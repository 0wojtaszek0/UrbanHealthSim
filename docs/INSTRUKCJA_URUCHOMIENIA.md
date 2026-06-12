# Urban Health ABM – Instrukcja Uruchomienia

## 📋 Przegląd Systemu

Ten projekt implementuje **demograficzny model populacyjny oparta na agentach (ABM)** dla 50,000 obywateli, opierając się na polskiej strukturze demograficznej GUS.

### Główne cechy:
- ✅ **50,000 agentów** z realistyczną polską piramidą wieku (0–90 lat)
- ✅ **Architektura OOP** z klasami: Citizen, Household, Zone, SimulationEngine
- ✅ **Tabele demograficzne**: śmiertelność i płodność zależne od wieku
- ✅ **Czynniki ryzyka niezależne od chorób**: palenie, otyłość, alkohol, etc.
- ✅ **Piramidy wieku** interaktywne (Plotly) w stylu GUS
- ✅ **Wizualizacje**: trendy populacji, gospodarstw, rozkład płci

---

## 🚀 Szybki Start

### 1. Aktywacja Virtual Environment

```bash
cd "/Users/wojciechofiara/Desktop/Studia/Projekt zespołowy/ABM_2.0 2"
source .venv/bin/activate
```

### 2. Instalacja Zależności

```bash
pip install -r requirements.txt
```

Wymagane pakiety:
- `pandas >= 2.0.0` – przetwarzanie danych
- `plotly >= 5.0.0` – interaktywne wizualizacje
- `openpyxl >= 3.1.0` – wczytywanie Excel
- `numpy >= 1.20.0` – obliczenia numeryczne
- `scipy >= 1.7.0` – funkcje statystyczne

### 3. Uruchomienie Symulacji

```bash
python3 main.py
```

Symulacja będzie:
1. Inicjować model choroby z **3 chorobami** (CVD, Lung Cancer, Hypercholesterolemia)
2. Tworzyć 50,000 syntetycznych obywateli
3. Uruchamiać 50-letnią symulację (600 miesięcy)
4. Zbierać statystyki rocznie
5. Generować interaktywne HTML wizualizacje (piramidy wieku, trendy populacji, gospodarstwach, rozkład płci)

Czas wykonania: **~15-30 minut** (zależy od maszyny)

---

## 📊 Dane Wyjściowe

Po uruchomieniu `python3 main.py`, w folderze pojawią się:

### Piramidy Wieku (w stylu GUS):
- **`piramida_wieku_rok_50.html`** – piramida ostatniego roku (statyczna)
- **`piramida_wieku_animowana.html`** – piramida animowana z suwakiem lat (0–50)

Właściwości:
- Mężczyźni po lewej (wartości ujemne)
- Kobiety po po prawej (wartości dodatnie)
- Grupy wieku co 5 lat (0–4, 5–9, ..., 85–89, 90+)
- Symetryczna oś X względem zera
- Minimalistyczny design GUS
- Tło białe, legenda czytelna

### Trendy Populacji:
- **`population_trends.html`** – populacja ogółem, chorobowość, niepełnosprawność
- **`households_trends.html`** – liczba gospodarstw, średnia wielkość
- **`gender_distribution.html`** – rozkład mężczyzn/kobiet w czasie

---

## 🏗️ Architektura Projektu

### Klasy Główne:

#### `Citizen` (citizen.py)
Reprezentuje pojedynczego obywatela.

**Atrybuty:**
- `id` – unikalny ID
- `sex` – "male" lub "female"
- `age_months` – wiek w miesiącach
- `age_years` – wiek w latach (właściwość)
- `alive` – czy żywy
- `household_id` – ID gospodarstwa
- `zone_id` – ID strefy
- `diseases` – słownik chorób (0/1)
- `risk_factors` – słownik czynników ryzyka (0/1)
- `disability_score` – wynik niepełnosprawności

**Czynniki ryzyka:**
```
- smoking (palenie)
- obesity (otyłość)
- physical_inactivity (brak aktywności)
- alcohol_abuse (nadużywanie alkoholu)
- high_cholesterol (wysoki cholesterol)
- hypertension_stage0 (przedkłopotliwy stan wstępny)
- family_history (genetyka)
```

**Metody:**
- `age_one_month()` – zwiększenie wieku o miesiąc
- `mortality_risk()` – obliczenie ryzyka śmierci
- `fertility_probability()` – prawdopodobieństwo urodzenia się
- `maybe_die(rng)` – losowe określenie śmierci
- `maybe_give_birth(rng)` – losowe określenie narodzin

#### `Household` (household.py)
Reprezentuje gospodarstwo domowe.

**Atrybuty:**
- `id` – unikalny ID
- `zone_id` – ID strefy
- `members` – lista ID obywateli

**Metody:**
- `add_member(citizen_id)` – dodanie członka
- `remove_member(citizen_id)` – usunięcie członka
- `size()` – liczba członków

#### `Zone` (zone.py)
Reprezentuje geograficzną strefę miasta.

**Atrybuty:**
- `id` – unikalny ID
- `environmental_parameters` – jakość powietrza, dostęp do opieki, etc.

**Parametry:**
```
- air_quality (0-1): czystość powietrza
- greenery_index (0-1): obszary zieleni
- healthcare_access (0-1): dostęp do opieki
- population_density (liczba/km²): zagęszczenie
```

#### `SimulationEngine` (simulation_engine.py)
Główny silnik symulacji.

**Atrybuty:**
- `citizens` – słownik obywateli
- `households` – słownik gospodarstw
- `zones` – słownik stref
- `disease_model` – model chorób
- `mortality_table` – tabela śmiertelności
- `fertility_table` – tabela płodności
- `yearly_stats` – statystyki roczne

**Metody:**
- `load_initial_population(filepath)` – wczytanie z Excel
- `_create_synthetic_population(size)` – tworzenie populacji syntetycznej
- `run(months)` – uruchomienie symulacji
- `step()` – jeden krok symulacji (1 miesiąc)
- `handle_deaths()` – obsługa śmiertelności
- `handle_births()` – obsługa narodzin
- `handle_household_splits()` – tworzenie nowych gospodarstw
- `collect_yearly_stats(year)` – zbieranie statystyk

---

## 📈 Tabele Demograficzne

### Tabela Śmiertelności (DEFAULT_MORTALITY_TABLE)
Zawiera miesięczne ryzyko śmierci dla każdego wieku (wiek: (male_rate, female_rate)).

Przykład:
```python
0: (0.0003, 0.0002),     # Niemowlęta: 0.03-0.02% / miesiąc
20: (0.00005, 0.00003),  # Dorośli: 0.005-0.003% / miesiąc
50: (0.00025, 0.00012),  # Wiek średni: 0.025-0.012% / miesiąc
80: (0.00550, 0.00300),  # Starcy: 0.55-0.30% / miesiąc
```

### Tabela Płodności (DEFAULT_FERTILITY_TABLE)
Zawiera roczne stopy płodności dla każdego wieku.

Przykład:
```python
15: 0.01,   # Nastolatki: 1% rocznie
25: 0.06,   # Młode dorosłe: 6% rocznie (szczyt)
35: 0.02,   # Średni wiek: 2% rocznie
45: 0.0005, # Po menopauzie: 0.05% rocznie
```

---

## 🔧 Konfiguracja Symulacji

W `main.py` można dostosować:

```python
engine.fertility_rate = 1.0                      # Mnożnik płodności
engine.mortality_multiplier = 1.0               # Mnożnik śmiertelności
engine.household_split_probability = 0.001      # Prawdopodobieństwo rozmieszczenia
```

---

## 📚 Struktura Populacji Syntetycznej

System generuje populację na podstawie polskiej piramidy GUS:

```
Wiek        % Populacji
0–9 lat     4.5%
10–19 lat   5.5%
20–29 lat   6.5% ← bulge demograficzny
30–39 lat   8.5% ← bulge demograficzny
40–49 lat   8.5% ← bulge demograficzny
50–59 lat   7.5%
60–69 lat   6.5%
70–79 lat   5.5%
80–89 lat   3.0%
90+ lat     1.0%
```

**Zastosowani seksualna:**
- Ogółem ~51% kobiet
- 65+ lat ~55-65% kobiet

**Generacja dzieci:**
- Dzieci (0–14) utworzone syntetycznie z realistycznym rozkładem
- Bez chorób przewlekłych (niemowlęta mają bardzo niskie ryzyko)
- Dodane do istniejących gospodarstw rodzinnych

---

## 🧬 Logika Choroby i Czynników Ryzyka

### Choroby (3 główne zaburzenia):
- **CVD (Cardiovascular Disease)** – prevalencja: 35.0%, waga niepełnosprawności: 0.25
- **Lung Cancer** – prevalencja: 4.5%, waga niepełnosprawności: 0.55
- **Hypercholesterolemia** – prevalencja: 25.0%, waga niepełnosprawności: 0.08

### Czynniki Ryzyka (niezależne od chorób):
Każdy obywatel ma własny profil ryzyka, niezależnie od chorób.

**Modyfikatory Śmiertelności:**
- Każda choroba: +5% do śmiertelności na chorobę
- Każdy czynnik ryzyka (smoking, alkohol): +15-30% do śmiertelności

---

## 🖥️ Wymagania Systemowe

- **Python:** 3.9+
- **RAM:** ≥4 GB (zwłaszcza dla 50,000 agentów × 50 lat)
- **Czas:** ~15-30 minut dla 50-letniej symulacji (zależy od CPU)

---

## 📖 Przykład: Uruchomienie Krótszej Symulacji

Aby szybko przetestować, edytuj `main.py`:

```python
# Zmień na krótszą symulację
engine.run(months=120)  # 10 lat zamiast 50

# Lub mniejszą populację
loaded = engine._create_synthetic_population(5000)  # 5k zamiast 50k
```

---

## 🐛 Rozwiązywanie Problemów

### Problem: Brakuje Plotly
**Rozwiązanie:**
```bash
pip install plotly
```

### Problem: Zbyt wolne
**Rozwiązanie:**
- Zmniejsz populację w `main.py`
- Skróć symulację (np. 10 lat zamiast 50)
- Zmień `engine.run(months=120)` na mniejszą liczbę

### Problem: Błędy importu
**Rozwiązanie:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 📝 Cytowanie

Jeśli używasz tego modelu w badaniach:

```
Urban Health ABM - Demographic Population Engine
50,000 agents, Polish GUS-inspired structure
Simulation Engine with Mortality, Fertility & Risk Factors
Generated: March 2, 2025
```

---

## 📧 Kontakt

Pytania dotyczące architektury lub modelu: zobacz kod źródłowy w:
- `citizen.py` – logika obywatela
- `simulation_engine.py` – logika symulacji
- `disease_model.py` – modelu choroby
- `visualization.py` – wizualizacji

---

### Nowe funkcjonalności

- **Modelowanie stanów zdrowia**: Symulacja uwzględnia różne stany zdrowia obywateli ("healthy", "exposed", "infected", "severe", "recovered") oraz ich przejścia w czasie.
- **Dynamiczna zmiana stanu zdrowia**: W trakcie symulacji obywatele mogą przechodzić między stanami zdrowia w oparciu o zdefiniowane prawdopodobieństwa przejść.

---

**Powodzenia w symulacji! 🚀**

---

## 📋 RAPORT: CHOROBY W MODELU

### Podsumowanie Zdrowia Populacji

Model demograficzny bierze pod uwagę **3 główne choroby przewlekłe**, które są najczęstsze w populacji:

| Lp. | Choroba | Prevalencja | Waga Niepełnosprawności | Opis |
|-----|---------|-------------|------------------------|------|
| 1 | **CVD (Choroba sercowo-naczyniowa)** | 35.0% | 0.25 | Najczęstsza choroba (35% populacji). Obejmuje zawały, udary i zaburzenia rytmu serca. Główny czynnik ryzyka śmiertelności. W modelu ma znaczący wpływ na niepełnosprawność (0.25). |
| 2 | **Lung Cancer (Rak płuca)** | 4.5% | 0.55 | Najpoważniejsza choroba z największym wpływem na niepełnosprawność (0.55). Typowo diagnozowana w zaawansowanych stadiach. Bardzo wysoki wpływ na wczesną śmiertelność. |
| 3 | **Hypercholesterolemia** | 25.0% | 0.08 | Drugorzędna choroba (25% populacji). Wysoki cholesterol jest głównymi czynnikiem ryzyka CVD. W modelu ma niski bezpośredni wpływ na niepełnosprawność (0.08) ale pośrednio zwiększa ryzyko inne choroby. |

### Statystyki Epidemiologiczne

- **Całkowita prevalencja kombinacji**: ~64.5% populacji ma co najmniej jedną z trzech chorób
- **Średnia liczba chorób na osobę**: ~1.64 chorób
- **Rozkład wielomorbidności**: CVD i Hypercholesterolemia często współwystępują; Lung Cancer jest niezależny

### Wpływ na Symulację

1. **Śmiertelność**: Każda choroba zwiększa ryzyko śmierci
2. **Niepełnosprawność**: Suma wag chorób (_disability score_) dla każdej osoby
3. **Dynamika populacji**: Choroby wpływają na ogólną populację i strukturę wiekową

### Czynniki Ryzyka

Poza trzema modelowanymi chorobami, obywatele mają także czynniki ryzyka niezależne:
- Palenie
- Otyłość
- Brak aktywności fizycznej
- Nadużywanie alkoholu
- Wysoki cholesterol
- Historia rodzinna

Te czynniki mogą zwiększać ryzyko zarówno choroby, jak i śmiertelności.

---

**Data raportu**: 8 kwietnia 2026  
**Liczba chorób w modelu**: 3  
**Liczba parametrów demograficznych**: ~50  
**Liczba agentów**: 50,000  
**Okres symulacji**: 50 lat (600 miesięcy)
