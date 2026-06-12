# Analiza wyników ABM gridsearch (bez risk factors)

Folder zawiera wizualizacje oparte o nowy gridsearch **`gridsearch_full_abm_no_rf.py`** (z folderu nadrzędnego), który uruchamia pełny ABM dla 144 punktów siatki 12×12, ale z wyłączonymi risk factors (wszyscy agenci mają `RF=0`).

Różnica względem analogicznych skryptów w folderze nadrzędnym (`piramida_porownanie_ryzyko.py`, `populacja_w_czasie.py`):
- Punkty kalibracji pochodzą z **prawdziwego ABM optimum** (FM=1.927, MM=1.009), nie z proxy (FM=2.118, MM=1.127)
- Mieszany tryb RF dobrany pod cel każdej wizualizacji (zob. tabela poniżej)

## Zawartość

| Plik | Tryb RF | Opis | Runtime |
|------|---------|------|---------|
| `piramidy_3x3_no_rf.py` | **bez RF** | Siatka 3×3 piramid (9 ABM) — izoluje efekty demograficzne | ~16 min |
| `piramida_porownanie_z_rf.py` | **z RF** | 2 piramidy: ABM optimum vs dolny-środkowy — pokazuje pełen efekt selekcji | ~10 min |
| `populacja_w_czasie_no_rf.py` | **bez RF** | Trajektorie 50 lat dla tych samych 2 punktów (czyste demograficznie) | ~10 min |
| `graf_ryzyko_choroby.py` | n/d | Graf RF→choroby (pokazuje macierz β, niezależny od symulacji) | ~5s |

### Dlaczego mieszany tryb RF?

- **3×3 grid bez RF** — w 9 punktach na ekstremach FM/MM chcemy zobaczyć czysty efekt demograficzny bez zaciemniania przez różną prevalencję RF w różnych populacjach
- **Porównanie 2 piramid z RF** — tu chcemy pokazać "wycinanie" górnej części piramidy przez Cox-amplifikację dla palaczy/otyłych. Bez RF efekt byłby pomijalny.

## Punkty kalibracji

| Punkt | FM | MM | ABM score (bez RF) | Charakter |
|-------|----|----|-------------------|-----------|
| **ABM OPTIMUM** | 1.927 | 1.009 | **−0.88%** | najbliżej 0 w gridsearch ABM |
| DOLNY-ŚRODKOWY 3×3 | 1.545 | 1.600 | **−26.5%** | wysokie MM, środkowe FM |

Stare optimum proxy (FM=2.118, MM=1.127) daje w ABM bez RF **+6.93%**, co potwierdza że proxy systematycznie się myli z dala od MM≈1.0.

## Jak uruchomić

```bash
cd analiza_ABM_gridsearch

# Graf RF → choroby (najszybsze, ~5s)
python graf_ryzyko_choroby.py

# Piramidy 3×3 bez RF (9 symulacji, ~16 min)
python piramidy_3x3_no_rf.py

# Porównanie 2 piramid Z RF (2 symulacje, ~10 min)
python piramida_porownanie_z_rf.py

# Trajektorie ludności bez RF (2 symulacje, ~10 min)
python populacja_w_czasie_no_rf.py
```

## Generowane pliki HTML

| Plik | Tryb RF | Co pokazuje |
|------|---------|-------------|
| `piramidy_3x3_no_rf.html` | bez RF | 9 piramid w siatce 3×3 z adnotacjami score%, mediana wieku, prevalencje |
| `piramida_porownanie_z_rf.html` | **z RF** | 2 piramidy z pełnym efektem selekcji (Cox-amplifikacja widoczna) |
| `populacja_w_czasie_no_rf.html` | bez RF | Wykresy liniowe M/F/total 50 lat |
| `graf_ryzyko_choroby.html` | n/d | Sankey + sieć dwudzielna + heatmapa HR (7 RF × 2 choroby) |

## Źródło punktów kalibracji

`gridsearch_full_abm_no_rf_20260511_114958.json` w folderze nadrzędnym (144 wyniki ABM).
