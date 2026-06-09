# Evaluation

LazyCook includes a lightweight offline evaluation script:

```bash
python scripts/evaluate_recommendations.py
```

The script reads `data/eval_cases.json`, sends each case through `RecommendationService`, prints the top 3 recipe names, and summarizes ranking quality metrics.

## Evaluation Cases

Each case can define:

- `label`: optional human-readable case name.
- `difficulty`: case category, such as `basic`, `alias`, `fuzzy`, `preference`, `time_limit`, or `hard_negative`.
- `ingredients`: input fridge ingredients.
- `time_limit`: optional cooking time limit.
- `preferences`: optional recommendation preferences.
- `expected_contains`: acceptable recipe names that should appear in the top 3.
- `expected_not_contains`: recipe names that should not appear in the top 3.
- `expected_tags`: tags that should be represented by the top 3 recipes.
- `hard_negative`: whether bad matches should count toward hard negative metrics.

## Metrics

### Hit@3

`Hit@3` is the fraction of cases where at least one recipe from `expected_contains` appears in the top 3 recommendations.

Higher is better.

### Bad@3

`Bad@3` is the fraction of cases where at least one recipe from `expected_not_contains` appears in the top 3 recommendations.

Lower is better.

### Hard Negative Bad@3

`Hard negative Bad@3` is `Bad@3` calculated only across cases marked with `hard_negative: true`.

Lower is better. This metric is useful for preference and exclusion cases where an obviously wrong recommendation would be more damaging.

### Tag Match

`Tag match` is the fraction of cases where at least one tag from `expected_tags` appears in the combined tags of the top 3 recommendations.

Higher is better.

### Non-basic Case Ratio

`Non-basic case ratio` is the share of evaluation cases whose `difficulty` is not `basic`. It is a coverage signal, not a quality score.

## Example Output

```text
Overall metrics:
- Hit@3: 1.000
- Bad@3: 0.000
- Hard negative Bad@3: 0.000
- Tag match: 1.000
- Non-basic case ratio: 0.455
```

The exact values can change when recipe data, aliases, preferences, or scoring weights change.
