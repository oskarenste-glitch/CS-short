# WG Organizer (simplified draft)

A Streamlit app for a flat share: split costs fairly, organise chores and shopping, and find dishes everyone at home can eat. It learns from your ratings what each flatmate likes.

## Run it

You need Python 3.10 or newer.

```bash
cd wg-simple
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Tests for the money and cooking rules: `python -m pytest`

## How it covers the requirements

| Requirement | Where |
|---|---|
| Data via API / database | ECB exchange rates via the Frankfurter API (`fx.py`), SQLite database (`db.py`), recipe data (`data/recipes.csv`) |
| Visualisation | Fair Split: spending per month and category, balances per person |
| User interaction | Every page: forms, filters, ratings, ticking off chores and items |
| Machine learning | `ml.py`: one ridge regression per flatmate predicts ratings from cuisine, diet, tags and cooking time |

## Files

| File | Contents |
|---|---|
| `app.py` | Start page: first setup, "who's home today", navigation |
| `views/split.py` | Fair Split: expenses, charts, who pays whom |
| `views/house.py` | Cleaning rota and shopping list |
| `views/cooking.py` | Suggestions, ratings, what the model learned |
| `views/flatmates.py` | Food preferences, adding and removing flatmates |
| `logic.py` | Rules as plain functions: balances, settling up, rota, diet/allergy/dislike checks |
| `ml.py` | Machine learning |
| `fx.py` | Exchange rates |
| `db.py` | Database tables and helpers |
| `data/recipes.csv` | 45 recipes |
| `tests/test_logic.py` | Tests for `logic.py` |

Data is stored in `wg.sqlite` next to `app.py`. There is no login.

## Use of AI

This draft was generated with Claude (Anthropic) in November 2026, based on an earlier vibe-coded version. Each file is marked accordingly.
