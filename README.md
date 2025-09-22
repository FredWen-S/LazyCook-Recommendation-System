# LazyCook-Recommendation-System
A cooking recommendation system that suggests recipes based on available ingredients. Includes toy prototype, NLP-enhanced version, and production-ready architecture.

## Run API
uvicorn api:app --reload

### Swagger
http://127.0.0.1:8000/docs

### Example request
POST /v1/recommend
{
  "fridge": ["番茄", "鸡蛋", "蒜"],
  "k": 3,
  "time_limit": 15
}
