"""Database: one SQLite file (wg.sqlite) with one table per kind of data.

Lists (who shares an expense, allergies, ...) are stored as comma-separated text, e.g. "1,3".
"""
# Draft generated with Claude (Anthropic), November 2026. Cite it if you reuse this code.
import os
import sqlite3
from contextlib import closing

import pandas as pd

DB_PATH = os.environ.get("WG_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "wg.sqlite"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS members (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL,
    diet      TEXT NOT NULL DEFAULT 'any',   -- any / pesce / veg / vegan
    allergies TEXT NOT NULL DEFAULT '',      -- e.g. 'Gluten,Nuts'
    dislikes  TEXT NOT NULL DEFAULT '',      -- e.g. 'tofu,mushrooms'
    cuisines  TEXT NOT NULL DEFAULT ''       -- favourite cuisines, e.g. 'italian,indian'
);
CREATE TABLE IF NOT EXISTS expenses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT,
    category   TEXT,
    date       TEXT,                          -- 'YYYY-MM-DD'
    amount     REAL,                          -- as typed in ...
    currency   TEXT,                          -- ... in this currency
    amount_chf REAL,                          -- converted once when saved, never again
    payer      INTEGER,                       -- member id
    shared_by  TEXT                           -- member ids, e.g. '1,2,4'
);
CREATE TABLE IF NOT EXISTS ratings (
    member INTEGER,
    recipe TEXT,
    score  INTEGER,                           -- 1 to 10
    date   TEXT,
    PRIMARY KEY (member, recipe)              -- one rating per person and dish; a new one replaces the old
);
CREATE TABLE IF NOT EXISTS chores (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT,
    every_days INTEGER,
    due        TEXT,
    assignee   INTEGER
);
CREATE TABLE IF NOT EXISTS shopping (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT,
    done INTEGER DEFAULT 0                    -- 0 = still to buy, 1 = in the trolley
);
"""

# create the tables once, when the app starts
with closing(sqlite3.connect(DB_PATH)) as _con:
    _con.executescript(SCHEMA)


def run(sql: str, params=()) -> None:
    """Run a statement that changes data (INSERT, UPDATE, DELETE)."""
    with closing(sqlite3.connect(DB_PATH)) as con, con:  # second 'con' commits automatically
        con.execute(sql, params)


def table(sql: str, params=()) -> pd.DataFrame:
    """Run a SELECT and get the result as a pandas DataFrame."""
    with closing(sqlite3.connect(DB_PATH)) as con:
        return pd.read_sql_query(sql, con, params=params)


def members() -> pd.DataFrame:
    return table("SELECT * FROM members ORDER BY id")


def names() -> dict:
    """{member id: name}, used everywhere to show names instead of ids."""
    m = members()
    return dict(zip(m["id"], m["name"]))
