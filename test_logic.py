"""Tests for logic.py. Run with:  python -m pytest"""
# Draft generated with Claude (Anthropic), November 2026. Cite it if you reuse this code.
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import logic  # noqa: E402


def test_balances_split_equally():
    # Oskar (1) pays 90 for three people -> he gets 60 back, the other two owe 30 each
    bal = logic.balances([1, 2, 3], [(1, 90.0, [1, 2, 3])])
    assert bal == {1: 60.0, 2: -30.0, 3: -30.0}


def test_settle_brings_everyone_to_zero():
    bal = logic.balances([1, 2, 3], [(1, 90.0, [1, 2, 3]), (2, 30.0, [2, 3])])
    transfers = logic.settle(bal)
    for frm, to, value in transfers:  # book every transfer like the "Paid" button does
        bal[frm] += value
        bal[to] -= value
    assert all(abs(v) < 0.01 for v in bal.values())


def test_rota_wraps_around():
    assert logic.next_assignee([1, 2, 3], 2) == 3
    assert logic.next_assignee([1, 2, 3], 3) == 1


def test_blockers():
    curry = {"name": "Chickpea Curry", "ingredients": "2 cans chickpeas; 1 eggplant", "diet": "vegan", "allergens": ""}
    steak = {"name": "Steak", "ingredients": "beef", "diet": "meat", "allergens": ""}
    vegan = {"name": "Mira", "diet": "vegan", "allergies": "", "dislikes": ""}
    picky = {"name": "Oskar", "diet": "any", "allergies": "", "dislikes": "chickpea, egg"}
    assert logic.blockers(curry, [vegan]) == []
    assert logic.blockers(steak, [vegan]) == ["Mira is vegan"]
    # 'chickpea' also blocks 'chickpeas', but 'egg' must not block 'eggplant'
    assert logic.blockers(curry, [picky]) == ["Oskar doesn't like chickpea"]
