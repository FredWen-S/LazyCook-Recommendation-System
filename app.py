from recommend import recommend

if __name__ == "__main__":
    s = input("输入冰箱里的食材，用空格分隔（例：番茄 鸡蛋 西兰花）：")
    fridge = s.strip().split()
    results = recommend(fridge, k=5, time_limit=15)
    for i, r in enumerate(results, 1):
        need = "、".join(r["need_more"])
        print(f"{i}. {r['name']}  分数{r['score']}  命中{r['hit']} 缺{r['miss']}  "
              f"用时{r['time']}min  标签{r['tags']}")
        if need:
            print(f"   还缺：{need}")
