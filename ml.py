"""Machine learning: predict how much a flatmate will like a recipe, from the dishes they rated before.

1. Every recipe becomes a row of numbers (features): one 0/1 column per cuisine, diet and tag, plus cooking time.
2. For each person, a ridge regression learns one weight per column from their ratings (1-10).
   Ridge = linear regression with a "brake": with only a few ratings it keeps the weights small
   instead of jumping to extreme conclusions (less overfitting).
3. The model then predicts a rating for every recipe the person hasn't rated yet.
"""
# Draft generated with Claude (Anthropic), November 2026. Cite it if you reuse this code.
import pandas as pd
from sklearn.linear_model import Ridge

MIN_RATINGS = 3   # fewer ratings than this: nothing sensible to learn yet
NEUTRAL = 5.5     # middle of the 1-10 scale, used when there is no model


def features(recipes: pd.DataFrame) -> pd.DataFrame:
    """One row per recipe (index = recipe id), one numeric column per property."""
    X = pd.get_dummies(recipes[["cuisine", "diet"]], dtype=float)        # e.g. cuisine_italian = 1 or 0
    tags = recipes["tags"].fillna("").str.get_dummies(sep=",").add_prefix("tag_")  # e.g. tag_quick
    X = pd.concat([X, tags], axis=1)
    X["hours"] = recipes["minutes"] / 60
    X.index = recipes["id"]
    return X


def train(ratings: pd.DataFrame, X: pd.DataFrame):
    """ratings = one person's rows with columns 'recipe' and 'score'. Returns a trained model or None."""
    ratings = ratings[ratings["recipe"].isin(X.index)]  # ignore ratings of recipes that no longer exist
    if len(ratings) < MIN_RATINGS:
        return None
    model = Ridge(alpha=1.0)
    model.fit(X.loc[ratings["recipe"]], ratings["score"])
    return model


def predict(model, X: pd.DataFrame) -> pd.Series:
    """Predicted rating (1-10) for every recipe in X."""
    return pd.Series(model.predict(X), index=X.index).clip(1, 10)


def explain(model, X: pd.DataFrame, k: int = 3) -> tuple[list, list]:
    """The k properties that raise / lower this person's predicted rating the most."""
    weights = pd.Series(model.coef_, index=X.columns).sort_values()
    nice = lambda col: col.replace("cuisine_", "").replace("diet_", "").replace("tag_", "").replace("hours", "long cooking")
    likes = [nice(c) for c, w in weights[::-1].items() if w > 0.1][:k]
    dislikes = [nice(c) for c, w in weights.items() if w < -0.1][:k]
    return likes, dislikes
