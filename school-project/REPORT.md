# МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ

## Московский Авиационный Институт
### (Национальный исследовательский университет)

---

**Институт №8** — «Компьютерные науки и прикладная математика»  
**Кафедра 806** — «Вычислительная математика и программирование»

---

## Лабораторная работа №1

по дисциплине **«Библиотеки и фреймворки Python»**

### Тема:
«Приём работ и расширяемые
анализаторы»

---

| | |
|---|---|
| **Студент:** | Лисняк А.В. |
| **Группа:** | М8О-103СВ-26 |
| **Преподаватель:** | Халид С.А. |
| **Оценка:** | |
| **Дата:** | 2026-10-15 |

---

**Москва, 2026**

---






**Траектория:** Python Core (основной вариант)  
**Уровень:** основной (углубления не выбирались)  


---

## 1. Краткое описание

Реализован устанавливаемый Python-пакет `school-lab`, который:

- принимает студенческие сдачи из JSONL-файла или in-memory источника;
- валидирует схему, обязательные поля, часовой пояс и AI-декларацию;
- сохраняет неизменяемые версии сдачи с устойчивым SHA-256-отпечатком;
- различает `accepted`, `duplicate` и `conflict` без перезаписи исходной записи;
- запускает сменные анализаторы через единый контракт `Analyzer`;
- формирует `AnalysisReport` с `analyzer_id`, `analyzer_version`, `config_hash`
  и проверяемыми ссылками `Evidence` на строки исходного текста.
- читает описания заданий из assignments.json (Assignment, load_assignments)

Третий анализатор `DeclarationAnalyzer` подключён **только регистрацией**
в реестре фабрик — центральный сервис `AnalysisService` не менялся.


## 2. Команды проверки

```bash
$ python -m pytest
39 passed in 0.04s

$ ruff check .
All checks passed!

$ mypy src
Success: no issues found in 11 source files
```

**Проверка установки в чистом окружении:**

```bash
$ cd /tmp
$ python3.12 -m venv clean_env
$ source clean_env/bin/activate
$ pip install /Users/a.lisnyak/PycharmProjects/school-project
...
Successfully built school-lab
Successfully installed school-lab-0.1.0

$ python -c "from school_lab import parse_submission, Submission; print('import ok')"
import ok

$ school-lab --help
usage: school-lab [-h] {import} ...

Приём учебных сдач из JSONL

positional arguments:
  {import}
    import    Импорт файла сдач

options:
  -h, --help  show this help message and exit
```
---

## 3. Демонстрация CLI

Файл `data/submissions.jsonl`:
команда  `school-lab import data/submissions.jsonl`:

```
  {"accepted": ["sub-001", "sub-002", "sub-003"], "duplicate": [], "errors": []}
```



### 

Файл `invalid_submissions.jsonl`:
команда  `school-lab import data/invalid_submissions.jsonl`:
```
{"accepted": [], "duplicate": [], "errors": [{"line_no": 1, "code": "schema_error", "field": "student_id", "message": "Ожидается непустая строка"}, {"line_no": 2, "code": "invalid_json", "field": "json", "message": "Ошибка JSON около столбца 2"}, {"line_no": 3, "code": "unsupported_version", "field": "schema_version", "message": "Поддерживается версия схемы 1"}, {"line_no": 4, "code": "schema_error", "field": "submitted_at", "message": "Часовой пояс обязателен"}, {"line_no": 5, "code": "schema_error", "field": "text/code", "message": "Текст или код должны быть непустыми"}]}
1
```



---

## 4. Измерения

Скрипт измерений: `scripts/benchmark.py`. Запуск:

```bash
$ python scripts/benchmark.py
```

### 4.1. Измерение 1: `parse_submission`

```
parse_submission: 10000 итераций за 0.1090 с (~10.9 мкс/вызов)
```

### 4.2. Измерение 2: `submission_hash` (SHA-256)

```
submission_hash (SHA-256): 10000 итераций за 0.0806 с (~8.1 мкс/вызов)
```


### 4.3. Измерение 3: `min` vs `sorted()[0]`

```
sorted(set)[0]: 100000 итераций за 9.5300 с
min(set):       100000 итераций за 1.6632 с
Ускорение min: 5.7x
```

---

---

## 5. Воспроизводимость

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

python -m pytest
ruff check .
mypy src
python scripts/benchmark.py