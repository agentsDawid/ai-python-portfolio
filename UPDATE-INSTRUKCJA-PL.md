# Aktualizacja portfolio Zensical — automatyczne listy projektów

## Co zawiera paczka

- generator kart na stronie głównej i stronie Projects na podstawie metadanych każdego `index.md`;
- automatyczne budowanie sekcji `nav` w `zensical.toml` z tych samych metadanych;
- sortowanie najpierw po `date` malejąco, a dla projektów bez daty — alfabetycznie na końcu;
- `featured: true/false` niezależnie od daty;
- wspólną komendę `scripts/site.py`, która generuje listy przed `zensical serve` albo `zensical build`;
- workflow GitHub Actions uruchamiający tę samą ścieżkę podczas publikacji;
- folder dla każdego projektu z `index.md` i `files/`.

## Wdrożenie na istniejącym repozytorium

1. Zrób kopię zapasową repozytorium.
2. Paczka aktualizacyjna ma ścieżki względne względem katalogu repozytorium: rozpakuj ją bezpośrednio do katalogu głównego obecnego repozytorium, zgadzając się na nadpisanie wskazanych plików. Nie twórz dodatkowego, zagnieżdżonego folderu `ai-python-portfolio`.
3. Usuń stare, płaskie strony projektu, jeśli pozostały po wcześniejszej wersji:
   - `docs/projects/tia-rename-assistant.md`
   - `docs/projects/python-data-experiments.md`
   - `docs/projects/local-ai-automation.md`
4. Zainstaluj zależności:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Uruchom podgląd przez wrapper:

   ```powershell
   python scripts/site.py serve
   ```

Nie uruchamiaj samego `zensical serve`, jeśli chcesz, aby przed podglądem zostały odświeżone karty i nawigacja.

## Dodawanie następnego projektu

Utwórz folder `docs/projects/nazwa-projektu/`, dodaj w nim `index.md` oraz `files/`. Na początku `index.md` umieść metadane w tym formacie:

```yaml
---
title: "Project title"
description: "Short description for the project card."
date: 2026-10-22
featured: false
categories:
  - Python
  - Data Analysis
---
```

Użyj rzeczywistej daty projektu lub publikacji w formacie `YYYY-MM-DD`. `featured: true` umieszcza projekt w sekcji Featured; `false` — w Other projects. Generator sortuje każdą sekcję od najnowszego projektu do najstarszego. Nie potrzeba pola `order` ani ręcznego wpisu w nawigacji.

Następnie uruchom `python scripts/site.py serve` albo `python scripts/site.py build`. Generator automatycznie odświeży stronę główną, listę projektów i `nav` w `zensical.toml`.

## Uwaga o istniejących datach

Nie wszystkie dotychczasowe projekty miały wiarygodną datę w plikach źródłowych, więc nie zostały one wymyślone. Generator wyświetla ostrzeżenie i umieszcza projekty bez `date` po projektach z datą, sortując je alfabetycznie. Uzupełnij datę w metadanych, kiedy ją potwierdzisz.
