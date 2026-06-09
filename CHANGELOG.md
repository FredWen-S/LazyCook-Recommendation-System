# Changelog

## v0.1.0

Initial release candidate.

Completed capabilities:

- FastAPI recommendation service with `/health`, `/docs`, `/demo/`, and `/v1/recommend`.
- Ingredient alias normalization.
- Default deterministic hashing embedding provider.
- Optional sentence-transformers provider in `requirements-ml.txt`.
- Rule-based preferences: `avoid`, `diet`, `meal_type`, and `max_missing`.
- Recommendation explanations with matched and missing ingredients.
- Recipe data validation script.
- Offline recommendation evaluation script with Hit@3, Bad@3, hard negative, and tag match metrics.
- Pytest suite for API, service behavior, data validation, evaluation, and embedding providers.
- Static browser demo.
- Dockerfile for lightweight default deployment.
- GitHub Actions CI matching local validation commands.
- Release-facing README and docs.
