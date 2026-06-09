# Architecture

LazyCook is a small FastAPI service backed by JSON recipe data and deterministic local embeddings.

## Request Flow

```text
alias normalization -> candidate filtering -> embedding similarity -> ingredient coverage -> preference rules -> scoring -> explanation
```

## 1. Alias Normalization

The service loads `data/aliases.json` and normalizes request ingredients before scoring.

Examples:

- `西红柿 -> 番茄`
- `蛋 -> 鸡蛋`
- `剩饭 -> 米饭`
- `素食 -> 素菜`

Normalization also deduplicates repeated ingredients after trimming whitespace.

## 2. Candidate Filtering

The service loads recipes from `data/recipes.json` and removes recipes that cannot satisfy hard request constraints:

- `time_limit`: recipes with a longer `cook_time` are excluded.
- `preferences.avoid`: recipes matching avoided terms in name, tags, or ingredients are excluded.
- `preferences.max_missing`: recipes requiring too many missing ingredients are excluded.

## 3. Embedding Similarity

The default provider is `hashing`. It is deterministic, offline, and lightweight.

The service embeds normalized fridge ingredients and each recipe ingredient list, then computes cosine similarity. The cosine value is normalized to the `0..1` range and returned as `similarity_score`.

`sentence-transformers` is optional and stays outside the default install path in `requirements-ml.txt`.

## 4. Ingredient Coverage

Ingredient coverage measures the direct overlap between normalized fridge ingredients and normalized recipe ingredients:

```text
matched recipe ingredients / total recipe ingredients
```

This value is returned as `ingredient_coverage`.

## 5. Preference Rules

Preferences are rule-based:

- `avoid` filters matching recipes.
- `diet` adds a small tag boost.
- `meal_type` adds a small tag boost.
- `max_missing` filters recipes above the missing ingredient limit.

These rules do not call an LLM and do not replace the default hashing embedding provider.

## 6. Scoring

The final score combines:

- ingredient coverage
- embedding similarity
- time fit
- optional preference tag boost

Current weights are defined in `app/services/recommendation_service.py`:

```text
ingredient_coverage: 0.55
similarity_score: 0.35
time_score: 0.10
```

The final `score` is clamped to the `0..1` range and rounded.

## 7. Explanation

Each recommendation includes a short `reason` with:

- matched ingredients
- missing ingredients
- estimated cook time
- a simple fit statement based on coverage

The explanation is generated locally from scored recipe data.
