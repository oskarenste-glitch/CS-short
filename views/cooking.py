"""Cooking: recipes that suit everyone at home, ranked by what the app has learned from your ratings."""
# Draft generated with Claude (Anthropic), November 2026. Cite it if you reuse this code.
import os
from datetime import date

import pandas as pd
import streamlit as st

import db
import logic
import ml

SHOW = 15  # how many suggestions to show


@st.cache_data  # read the CSV once, not on every click
def load_recipes() -> pd.DataFrame:
    return pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "data", "recipes.csv"))


st.title("🍝 Cooking")
recipes = load_recipes()
members = db.members()
names = dict(zip(members["id"], members["name"]))
at_table = members[members["id"].isin(st.session_state.get("home", []))].to_dict("records")

if not at_table:
    st.info("Nobody is home today. Pick who's eating in the sidebar.")
    st.stop()
st.write("**At the table today:** " + ", ".join(p["name"] for p in at_table))

# ---------- filters ----------
a, b, c = st.columns([2, 1, 1])
query = a.text_input("Search", placeholder="e.g. pasta, curry, quick")
cuisine = b.selectbox("Cuisine", ["all"] + sorted(recipes["cuisine"].unique()))
max_minutes = c.selectbox("Max. time", [0, 20, 30, 45, 60], format_func=lambda t: "any" if t == 0 else f"{t} min")

shown = recipes
if query:
    text = (recipes["name"] + " " + recipes["ingredients"] + " " + recipes["tags"].fillna("")).str.lower()
    shown = shown[text.str.contains(query.lower(), regex=False)]
if cuisine != "all":
    shown = shown[shown["cuisine"] == cuisine]
if max_minutes:
    shown = shown[shown["minutes"] <= max_minutes]

# ---------- hard rules first: diet, allergies, dislikes ----------
reasons = {r["id"]: logic.blockers(r, at_table) for r in shown.to_dict("records")}
fits = shown[shown["id"].map(lambda rid: not reasons[rid])].copy()

# ---------- then machine learning: predicted rating of each person, averaged over the table ----------
X = ml.features(recipes)
ratings = db.table("SELECT * FROM ratings")
models = {m["id"]: ml.train(ratings[ratings["member"] == m["id"]], X) for m in members.to_dict("records")}


def expected_rating(person) -> pd.Series:
    """What this person will probably rate each recipe (1-10)."""
    model = models.get(person["id"])
    if model is not None:
        guess = ml.predict(model, X)
    else:  # not enough ratings yet: neutral, a bit higher for their favourite cuisines
        fav = logic.words(person["cuisines"])
        guess = pd.Series([ml.NEUTRAL + (1.5 if c in fav else 0) for c in recipes["cuisine"]], index=recipes["id"])
    # dishes the person already rated: use the real rating instead of a guess
    own = ratings[ratings["member"] == person["id"]].set_index("recipe")["score"]
    guess.update(own[own.index.isin(guess.index)].astype(float))
    return guess


table_scores = pd.concat([expected_rating(p) for p in at_table], axis=1).mean(axis=1)
fits["score"] = fits["id"].map(table_scores)
fits = fits.sort_values("score", ascending=False)

learning = [p["name"] for p in at_table if models.get(p["id"]) is not None]
st.subheader(f"Suits everyone ({len(fits)})")
st.caption("Sorted by the expected rating of everyone at the table. "
           + (f"Learned from the ratings of {', '.join(learning)}." if learning
              else f"Rate at least {ml.MIN_RATINGS} dishes each and the app starts learning what you like."))

for r in fits.head(SHOW).to_dict("records"):
    with st.expander(f"**{r['name']}** · ⭐ {r['score']:.1f} · {r['minutes']} min · {r['diet']} · {r['cuisine']}"):
        if isinstance(r["allergens"], str):
            st.caption("Contains: " + r["allergens"].replace(",", ", "))
        a, b = st.columns([1, 1.4])
        a.markdown("**Ingredients (4 servings)**\n" + "\n".join(f"- {i}" for i in r["ingredients"].split("; ")))
        b.markdown("**Method**\n" + "\n".join(f"{n}. {s}" for n, s in enumerate(r["steps"].split(" | "), 1)))

        if st.button("Add ingredients to shopping list", key=f"shop-{r['id']}"):
            for i in r["ingredients"].split("; "):
                db.run("INSERT INTO shopping (item) VALUES (?)", (f"{i} ({r['name']})",))
            st.toast("Added to the shopping list")

        with st.form(f"rate-{r['id']}"):
            a, b, c = st.columns([1.2, 2, 1])
            who = a.selectbox("Who rates?", [p["id"] for p in at_table], format_func=names.get)
            score = b.slider("How was it?", 1, 10, 7)
            if c.form_submit_button("Save rating"):
                # INSERT OR REPLACE: rating the same dish again overwrites the old rating
                db.run("INSERT OR REPLACE INTO ratings (member, recipe, score, date) VALUES (?, ?, ?, ?)",
                       (who, r["id"], score, date.today().isoformat()))
                st.rerun()

nofit = shown[~shown["id"].isin(fits["id"])]
if not nofit.empty:
    with st.expander(f"Not suitable today ({len(nofit)})"):
        st.dataframe(pd.DataFrame({"Recipe": nofit["name"], "Why not": nofit["id"].map(lambda rid: "; ".join(reasons[rid]))}),
                     hide_index=True)

# ---------- what the model learned (good to show in the video) ----------
st.subheader("What the app has learned")
for m in members.to_dict("records"):
    n = int((ratings["member"] == m["id"]).sum())
    model = models.get(m["id"])
    if model is None:
        st.write(f"**{m['name']}**: {n} rating(s), needs {ml.MIN_RATINGS} to start learning.")
    else:
        likes, dislikes = ml.explain(model, X)
        st.write(f"**{m['name']}** ({n} ratings): likes {', '.join(likes) or '–'} · less keen on {', '.join(dislikes) or '–'}")
