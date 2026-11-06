"""The rules of the app as plain functions: no Streamlit, no database, so they are easy to test."""
# Draft generated with Claude (Anthropic), November 2026. Cite it if you reuse this code.
import re


def ids(text) -> list[int]:
    """'1,3' -> [1, 3]"""
    return [int(x) for x in str(text).split(",") if x.strip()]


def words(text) -> list[str]:
    """'Tofu, mushrooms' -> ['tofu', 'mushrooms']"""
    return [w.strip().lower() for w in str(text).split(",") if w.strip()]


# ---------- Fair Split ----------
def balances(member_ids, expenses) -> dict:
    """expenses = list of (payer, amount_chf, shared_by ids).
    Result per person: positive = gets money back, negative = owes money."""
    bal = {m: 0.0 for m in member_ids}
    for payer, amount, shared_by in expenses:
        if not shared_by:
            continue
        bal[payer] = bal.get(payer, 0) + amount           # the payer laid out the whole amount
        for m in shared_by:
            bal[m] = bal.get(m, 0) - amount / len(shared_by)  # everyone sharing owes an equal part
    return bal


def settle(bal: dict) -> list[tuple]:
    """Few transfers that bring every balance to zero: the biggest debtor pays the biggest creditor, repeat.
    Returns (from, to, amount) tuples."""
    creditors = sorted([[m, v] for m, v in bal.items() if v > 0.005], key=lambda x: -x[1])
    debtors = sorted([[m, -v] for m, v in bal.items() if v < -0.005], key=lambda x: -x[1])
    transfers, i, j = [], 0, 0
    while i < len(debtors) and j < len(creditors):
        pay = min(debtors[i][1], creditors[j][1])  # as much as both sides allow
        transfers.append((debtors[i][0], creditors[j][0], round(pay, 2)))
        debtors[i][1] -= pay
        creditors[j][1] -= pay
        if debtors[i][1] < 0.005:   # this debtor is done, move on to the next
            i += 1
        if creditors[j][1] < 0.005:
            j += 1
    return [t for t in transfers if t[2] >= 0.01]


# ---------- Cleaning rota ----------
def next_assignee(member_ids: list, current):
    """The next person in flat order; after the last one it starts again at the first."""
    if current not in member_ids:
        return member_ids[0]
    return member_ids[(member_ids.index(current) + 1) % len(member_ids)]


# ---------- Cooking ----------
# How strict a person is / which people a recipe can serve. A recipe fits if its level >= the person's level.
DIET_LEVEL = {"any": 0, "meat": 0, "pesce": 1, "veg": 2, "vegan": 3}


def blockers(recipe: dict, people: list[dict]) -> list[str]:
    """Why a recipe doesn't work for the people at the table. Empty list = it suits everyone."""
    out = []
    text = (recipe["name"] + " " + recipe["ingredients"]).lower()
    for p in people:
        if DIET_LEVEL[p["diet"]] > DIET_LEVEL[recipe["diet"]]:
            out.append(f"{p['name']} is {p['diet']}")
        for a in set(words(p["allergies"])) & set(words(recipe["allergens"])):
            out.append(f"{p['name']} can't eat {a}")
        for w in words(p["dislikes"]):
            # whole words only (plural allowed): 'egg' blocks 'eggs' but not 'eggplant', 'pea' not 'peanut'
            if re.search(rf"\b{re.escape(w)}(s|es)?\b", text):
                out.append(f"{p['name']} doesn't like {w}")
    return out
