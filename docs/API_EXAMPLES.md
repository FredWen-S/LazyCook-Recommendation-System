# API Examples

LazyCook exposes one recommendation endpoint:

```http
POST /v1/recommend
Content-Type: application/json
```

All examples assume the service is running at `http://127.0.0.1:8000`.

## Basic Recommendation

```bash
curl -X POST http://127.0.0.1:8000/v1/recommend \
  -H "Content-Type: application/json" \
  -d '{"fridge":["番茄","鸡蛋","蒜"],"k":3,"time_limit":15}'
```

Request body:

```json
{
  "fridge": ["番茄", "鸡蛋", "蒜"],
  "k": 3,
  "time_limit": 15
}
```

## Alias Normalization

Inputs can use aliases from `data/aliases.json`. For example, `西红柿` normalizes to `番茄`, `蛋` normalizes to `鸡蛋`, and `剩饭` normalizes to `米饭`.

```json
{
  "fridge": ["西红柿", "蛋", "剩饭"],
  "k": 5
}
```

## Avoid Preference

`avoid` filters recipes when a term appears in the recipe name, tags, or ingredients.

```json
{
  "fridge": ["鸡蛋", "盐"],
  "k": 5,
  "time_limit": 10,
  "preferences": {
    "avoid": ["汤"],
    "max_missing": 2
  }
}
```

## Diet Preference

`diet` gives a small score boost when a requested term matches recipe tags.

```json
{
  "fridge": ["蒜", "油", "盐"],
  "k": 5,
  "time_limit": 10,
  "preferences": {
    "diet": ["素菜"],
    "max_missing": 1
  }
}
```

## Meal Type Preference

`meal_type` behaves like a tag preference and can boost recipes tagged as soup, noodles, cold dishes, and similar categories.

```json
{
  "fridge": ["面条", "蒜"],
  "k": 3,
  "time_limit": 15,
  "preferences": {
    "meal_type": "面",
    "max_missing": 3
  }
}
```

## Full Preference Request

```json
{
  "fridge": ["肉", "面条", "蒜", "橄榄油"],
  "k": 3,
  "time_limit": 20,
  "preferences": {
    "avoid": ["培根"],
    "diet": ["西式"],
    "meal_type": "面",
    "max_missing": 2
  }
}
```

## Response Fields

Each response includes:

- `query`: the validated request payload.
- `recommendations`: ranked recipes.
- `meta`: algorithm, provider, candidate, and scoring metadata.

Each recommendation includes:

- `id`, `name`, `ingredients`, `tags`, `cook_time`
- `matched_ingredients`, `missing_ingredients`
- `score`, `similarity_score`, `ingredient_coverage`, `time_score`
- `reason`

## Validation Rules

- `fridge` is required and must contain 1 to 50 non-blank strings.
- `k` defaults to `5` and must be between 1 and 20.
- `time_limit` is optional and must be between 1 and 240 when present.
- `preferences` is optional.
- Unknown request fields are rejected.
