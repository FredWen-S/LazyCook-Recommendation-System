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

# LazyCook Recommendation System

输入冰箱食材，返回可做菜谱（玩具级 / 课设级）。后端 FastAPI，前端一张 HTML。

## 运行方式

### 1) 本地直接跑（无 Docker）
```bash
# 激活虚拟环境后
pip install -r requirements.txt
uvicorn api:app --reload
# 打开 http://127.0.0.1:8000/docs
