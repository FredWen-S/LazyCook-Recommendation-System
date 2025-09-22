from recommend import recommend

def test_basic_hit():
    r = recommend(["番茄","鸡蛋"])
    assert any(x["name"]=="番茄炒蛋" for x in r)

def test_alias():
    r = recommend(["西红柿","蛋"])
    assert any(x["name"]=="番茄炒蛋" for x in r)

def test_time_filter():
    r = recommend(["西兰花","蒜"], time_limit=10)
    assert all((x["time"] or 0) <= 10 for x in r)

from recommend import recommend

def test_alias_hit():
    r = recommend(["西红柿","蛋"])  # 同义词应映射到 番茄、鸡蛋
    assert any(x["name"]=="番茄炒蛋" for x in r)

def test_only_few_ings():
    r = recommend(["鸡蛋","盐","蒜","番茄","米饭"], only_few_ings=True)  # 开启 ≤3 食材模式
    assert all(len(x["need_more"]) + x["hit"] <= 3 for x in r)  # 命中+缺料不超过3
