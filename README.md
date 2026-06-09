# LazyCook Recommendation System

LazyCook is a small FastAPI recipe recommendation service. It recommends simple dishes from fridge ingredients, explains matched and missing ingredients, supports lightweight preference rules, and ships with a one-page browser demo.

The default recommendation path is fully local and deterministic. It uses alias normalization plus a hashing embedding provider, so the API, tests, Docker image, and CI do not need ML model downloads.

## Features

- Ingredient-based recipe recommendations.
- Alias normalization such as `西红柿 -> 番茄`, `蛋 -> 鸡蛋`, `剩饭 -> 米饭`.
- Optional `k` and `time_limit` request controls.
- Optional preferences: `avoid`, `diet`, `meal_type`, `max_missing`.
- Deterministic hashing embeddings by default.
- Optional `sentence-transformers` provider through `requirements-ml.txt`.
- Data validation and recommendation evaluation scripts.
- FastAPI docs at `/docs` and browser demo at `/demo/`.

## Quick Start

These commands are the minimal clone-to-run path for the default lightweight setup.

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open:

- Health check: http://127.0.0.1:8000/health
- API docs: http://127.0.0.1:8000/docs
- Demo page: http://127.0.0.1:8000/demo/
- Recommendation API: `POST http://127.0.0.1:8000/v1/recommend`

The demo can also be opened directly from `frontend/index.html`; it calls `http://127.0.0.1:8000`.

## Demo Page

The `/demo/` page is a static HTML/CSS/JavaScript client served by FastAPI from `frontend/index.html`. It lets you enter fridge ingredients, tune recommendation controls, and inspect the returned recipes and explanations.

Screenshot placeholder:

```text
docs/images/demo.png
```

## API Example

```http
POST /v1/recommend
Content-Type: application/json
```

Request:

```json
{
  "fridge": ["西红柿", "蛋", "蒜"],
  "k": 3,
  "time_limit": 15,
  "preferences": {
    "avoid": ["培根"],
    "diet": ["家常"],
    "meal_type": "汤",
    "max_missing": 2
  }
}
```

Response shape:

```json
{
  "query": {
    "fridge": ["西红柿", "蛋", "蒜"],
    "k": 3,
    "time_limit": 15,
    "preferences": {
      "avoid": ["培根"],
      "meal_type": "汤",
      "diet": ["家常"],
      "max_missing": 2
    }
  },
  "recommendations": [
    {
      "id": "tomato-egg-soup",
      "name": "西红柿鸡蛋汤",
      "ingredients": ["番茄", "鸡蛋", "盐"],
      "matched_ingredients": ["番茄", "鸡蛋"],
      "missing_ingredients": ["盐"],
      "tags": ["汤", "家常"],
      "cook_time": 7,
      "score": 0.8455,
      "similarity_score": 0.7858,
      "ingredient_coverage": 0.6667,
      "time_score": 0.9067,
      "reason": "已匹配：番茄、鸡蛋；缺少：盐；预计 7 分钟。只需要补少量食材，适合作为当前推荐。"
    }
  ],
  "meta": {
    "algorithm": "embedding-cosine-v1",
    "embedding_provider": "hashing",
    "score_weights": {
      "ingredient_coverage": 0.55,
      "similarity_score": 0.35,
      "time_score": 0.1
    }
  }
}
```

More examples are in [docs/API_EXAMPLES.md](docs/API_EXAMPLES.md).

## Preferences

All preference fields are optional:

- `avoid: list[str]`: filters recipes when a term appears in the recipe name, tags, or ingredients.
- `meal_type: str`: gives a small score boost when it matches a recipe tag.
- `diet: list[str]`: gives a small score boost when any item matches recipe tags.
- `max_missing: int`: filters recipes that require more missing ingredients than allowed.

These controls are rule-based. They do not call an LLM.

## Evaluation Metrics

Run:

```bash
python scripts/evaluate_recommendations.py
```

Example output:

```text
Overall metrics:
- Hit@3: 1.000
- Bad@3: 0.000
- Hard negative Bad@3: 0.000
- Tag match: 1.000
- Non-basic case ratio: 0.455
```

The evaluation cases live in `data/eval_cases.json`. See [docs/EVALUATION.md](docs/EVALUATION.md) for metric definitions.

## Docker Usage

Build and run:

```bash
docker build -t lazycook .
docker run --rm -p 8000:8000 lazycook
```

Then open:

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/demo/

The Docker image installs only `requirements.txt`, starts `app.main:app`, and uses the hashing embedding provider by default.

## Local Validation

Run the same checks as CI:

```bash
python -m compileall app
python -m pytest
python scripts/validate_recipes.py
python scripts/evaluate_recommendations.py
```

On Windows PowerShell, the same commands work after activating `.venv`:

```powershell
python -m compileall app
python -m pytest
python scripts\validate_recipes.py
python scripts\evaluate_recommendations.py
```

## CI

GitHub Actions runs the same validation sequence:

- `python -m compileall app`
- `python -m pytest`
- `python scripts/validate_recipes.py`
- `python scripts/evaluate_recommendations.py`

CI installs `requirements.txt` only. It does not install `requirements-ml.txt` and does not download sentence-transformers models.

## Embedding Provider

Default provider:

```bash
export LAZYCOOK_EMBEDDING_PROVIDER=hashing
```

Windows PowerShell:

```powershell
$env:LAZYCOOK_EMBEDDING_PROVIDER = "hashing"
```

This is deterministic, offline, lightweight, and requires only `requirements.txt`.

Optional sentence-transformers provider:

```bash
python -m pip install -r requirements-ml.txt
export LAZYCOOK_EMBEDDING_PROVIDER=sentence-transformers
export LAZYCOOK_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Windows PowerShell:

```powershell
python -m pip install -r requirements-ml.txt
$env:LAZYCOOK_EMBEDDING_PROVIDER = "sentence-transformers"
$env:LAZYCOOK_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
```

`requirements-ml.txt` is intentionally optional so normal API usage, Docker, CI, and tests stay lightweight.

## Project Structure

```text
app/
  api/v1/routes/          FastAPI route handlers
  core/                   App configuration and logging helpers
  models/                 Recipe model
  nlp/                    Embedding providers and similarity helpers
  repositories/           JSON data access
  schemas/                Request/response schemas
  services/               Recommendation service
data/
  aliases.json            Ingredient aliases
  eval_cases.json         Recommendation evaluation cases
  recipes.json            Recipe data
docs/
  API_EXAMPLES.md         Extra request examples
  ARCHITECTURE.md         Recommendation flow
  EVALUATION.md           Evaluation cases and metrics
frontend/
  index.html              Browser demo
scripts/
  evaluate_recommendations.py
  validate_recipes.py
tests/
  pytest suite
```

## Architecture

At a high level:

```text
alias normalization -> candidate filtering -> embedding similarity -> ingredient coverage -> preference rules -> scoring -> explanation
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the detailed flow.

## Current Limitations

- Recipe data is intentionally small.
- Fuzzy input depends on aliases and hashing similarity, not deep language understanding.
- Preferences are rule-based and can be blunt, especially `avoid`.
- No user history, nutrition model, pantry quantities, cooking tools, or serving sizes.
- The frontend is a demo, not a full product UI.

## Future Improvements

- Expand recipe data and evaluation coverage.
- Add richer ingredient taxonomy and quantity handling.
- Add nutrition, servings, tool constraints, and pantry inventory.
- Add a stronger optional embedding or reranking mode while keeping hashing as the default.
- Add screenshots or a short demo recording under `docs/images/`.
