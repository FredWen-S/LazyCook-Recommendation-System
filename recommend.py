import json

def load_data():
    with open("data/recipes.json", "r", encoding="utf-8") as f:
        recipes = json.load(f)
    with open("data/aliases.json", "r", encoding="utf-8") as f:
        aliases = json.load(f)
    return recipes, aliases

def normalize(items, aliases):
    return [aliases.get(x.strip(), x.strip()) for x in items if x.strip()]

def score_recipe(fridge_set, recipe_ings):
    need = set(recipe_ings)
    hit = len(fridge_set & need)
    miss = len(need - fridge_set)
    coverage = hit / max(1, len(need))
    score = coverage - 0.05 * miss
    return round(score, 4), hit, miss

def recommend(fridge_items, k=5, time_limit=None, must_tags=None, ban_tags=None):
    recipes, aliases = load_data()
    fridge = set(normalize(fridge_items, aliases))
    must_tags = set(must_tags or [])
    ban_tags = set(ban_tags or [])

    candidates = []
    for r in recipes:
        if time_limit and r.get("time") and r["time"] > time_limit:
            continue
        if must_tags and not must_tags.issubset(set(r.get("tags", []))):
            continue
        if ban_tags and set(r.get("tags", [])) & ban_tags:
            continue
        s, hit, miss = score_recipe(fridge, r["ingredients"])
        candidates.append((s, hit, miss, r))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return [{
        "name": r["name"],
        "score": float(s),
        "hit": int(hit),
        "miss": int(miss),
        "need_more": list(set(r["ingredients"]) - fridge),
        "time": r.get("time"),
        "tags": r.get("tags", [])
    } for (s, hit, miss, r) in candidates[:k]]
